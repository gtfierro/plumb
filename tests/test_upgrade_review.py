"""Semantic review uses saved data and distinguishes behavior from provenance."""

import json
from pathlib import Path
import sys

import pytest
from rdflib import BNode, Graph, Literal, Namespace, OWL, RDF, RDFS
from rdflib.namespace import SH

from plumb.cli import main
from plumb.gen import generate
from plumb.gen.overlays import Overlay
from plumb.gen.review import compare_packages

EX = Namespace("urn:evolution#")
FIXTURE = Path(__file__).parent / "fixtures/evolution.ttl"


def source() -> Graph:
    return Graph().parse(FIXTURE)


def package(tmp_path: Path, name: str, graph: Graph, **kwargs) -> Path:
    directory = tmp_path / name
    generate(graph, directory, name="Evolution", **kwargs)
    return directory


def test_review_reports_effective_constraints_and_added_terms(tmp_path):
    before = package(tmp_path, "before", source())
    changed = source()
    changed.set((EX.MemberShape, SH["class"], EX.Dog))
    changed.set((EX.MemberShape, SH.maxCount, Literal(1)))
    changed.set((EX.CodeShape, SH.defaultValue, Literal("new")))
    changed.set((EX.Dog, RDFS.subClassOf, EX.Owner))
    changed.add((EX.Puppy, RDF.type, OWL.Class))
    changed.add((EX.Puppy, RDFS.subClassOf, EX.Dog))
    after = package(tmp_path, "after", changed)
    report = compare_packages(before, after)
    assert report.changed
    records = {
        (row.category, row.target, row.path, row.field): row for row in report.changes
    }
    assert records["class", str(EX.Puppy), None, "record"].kind == "added"
    assert records["class", str(EX.Dog), None, "parents"].after == [str(EX.Owner)]
    member = records["property", str(EX.Owner), str(EX.member), "max_count"]
    assert (member.before, member.after) == (3, 1)
    assert records["property", str(EX.Owner), str(EX.member), "range_groups"].after == [
        [str(EX.Dog)]
    ]
    assert records["property", str(EX.Owner), str(EX.code), "default_values"].after == [
        '"new"'
    ]
    inverse = compare_packages(after, before)
    assert any(
        row.kind == "removed" and row.target == str(EX.Puppy) for row in inverse.changes
    )
    assert report.to_json() == compare_packages(before, after).to_json()


@pytest.mark.parametrize("wrapper", [SH.node, SH["and"]])
def test_conjunctive_rewrites_change_provenance_without_changing_contract(
    tmp_path, wrapper
):
    before = package(tmp_path, "before", source())
    graph = source()
    graph.remove((EX.Owner, SH.property, EX.MemberShape))
    wrapped = BNode()
    graph.add((wrapped, SH.property, EX.MemberShape))
    if wrapper == SH.node:
        graph.add((EX.Owner, SH.node, wrapped))
    else:
        head = BNode()
        graph.add((EX.Owner, SH["and"], head))
        graph.add((head, RDF.first, wrapped))
        graph.add((head, RDF.rest, RDF.nil))
    after = package(tmp_path, "after", graph)
    report = compare_packages(before, after)
    assert report.changes == ()
    assert report.provenance_changes


def test_anonymous_query_changes_are_visible_without_source_id_noise(tmp_path):
    graph = source()
    query = BNode()
    graph.add((EX.Owner, SH.sparql, query))
    graph.add((query, SH.select, Literal("SELECT $this WHERE { FILTER(false) }")))
    before = package(tmp_path, "before", graph)
    # Fresh parse gives different blank IDs; reverse insertion tests iteration order.
    fresh = Graph().parse(data=graph.serialize(format="turtle"), format="turtle")
    reordered = Graph()
    for triple in reversed(list(fresh)):
        reordered.add(triple)
    same = package(tmp_path, "same", reordered)
    assert compare_packages(before, same).changes == ()
    node = fresh.value(EX.Owner, SH.sparql)
    assert node is not None
    fresh.set((node, SH.select, Literal("SELECT $this WHERE { FILTER(true) }")))
    after = package(tmp_path, "after", fresh)
    report = compare_packages(before, after)
    (change,) = report.changes
    assert (change.category, change.field) == ("support", str(SH.sparql))
    assert change.before[0]["enforcement"] == ["validation"]
    assert change.before[0]["value"] != change.after[0]["value"]


def test_review_tracks_alias_collisions_and_binding_status(tmp_path):
    overlay = Overlay(
        primary_namespace="urn:preferred#", rshift={str(EX.Owner): str(EX.member)}
    )
    before = package(tmp_path, "before", source(), overlay=overlay)
    graph = source()
    graph.add((Namespace("urn:preferred#").Owner, RDF.type, OWL.Class))
    after = package(tmp_path, "after", graph, overlay=overlay)
    report = compare_packages(before, after)
    assert any(
        row.target == str(EX.Owner)
        and row.field == "public_name"
        and row.after == "Owner_2"
        for row in report.changes
    )
    assert not any(row.category == "binding" for row in report.changes)


def test_provenance_and_dependencies_are_reviewed_without_imports(tmp_path):
    before = package(tmp_path, "before", source())
    after = package(tmp_path, "after", source())
    (before / "__init__.py").write_text("raise AssertionError('never import')")
    (after / "__init__.py").write_text("raise AssertionError('never import')")
    for directory, version, digest in [(before, "1", "a" * 64), (after, "2", "b" * 64)]:
        path = directory / "_symbols.json"
        data = json.loads(path.read_text())
        data["dependencies"] = [{"module": "unavailable_dependency", "sha256": digest}]
        data["ontology"]["version"] = version
        path.write_text(json.dumps(data))
        (directory / "_build.json").write_text(
            json.dumps(
                {
                    "format": 1,
                    "compiler": {"sha256": digest},
                    "sources": {"upstream": {"version": version, "sha256": digest}},
                }
            )
        )
    report = compare_packages(before, after)
    assert report.changes == ()
    assert {row.category for row in report.provenance_changes} == {
        "ontology",
        "compiler",
        "source",
        "dependency",
    }
    assert "unavailable_dependency" not in sys.modules


def test_cli_reports_changes_and_explains_missing_metadata(tmp_path, capsys):
    before = package(tmp_path, "before", source())
    assert main(["diff", str(before), str(before), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["changes"] == []
    assert main(["diff", str(before), str(before)]) == 0
    assert capsys.readouterr().out == "0 contract changes; 0 provenance changes\n"
    path = before / "_support.json"
    metadata = json.loads(path.read_text())
    metadata["format"] = 1
    path.write_text(json.dumps(metadata))
    with pytest.raises(SystemExit) as error:
        main(["diff", str(before), str(before)])
    assert error.value.code == 2
    message = capsys.readouterr().err
    assert "regenerate both versions" in message and "Traceback" not in message


def test_choice_order_and_anonymous_source_context_do_not_change_checks(tmp_path):
    before = package(tmp_path, "before", source())
    graph = source()
    head = graph.value(EX.CodeShape, SH["in"])
    assert head is not None
    second = graph.value(head, RDF.rest)
    assert second is not None
    graph.set((head, RDF.first, Literal("new")))
    graph.set((second, RDF.first, Literal("old")))
    # Moving the list changes anonymous incoming context but not allowed values.
    other = BNode()
    graph.remove((EX.CodeShape, SH["in"], head))
    graph.add((EX.Owner, SH["and"], other))
    graph.add((other, RDF.first, EX.AdditionalShape))
    graph.add((other, RDF.rest, RDF.nil))
    graph.add((EX.AdditionalShape, SH.property, EX.Choices))
    graph.add((EX.Choices, SH.path, EX.code))
    graph.add((EX.Choices, SH["in"], head))
    after = package(tmp_path, "after", graph)
    assert compare_packages(before, after).changes == ()


def test_review_includes_enum_and_enforcement_changes(tmp_path):
    graph = source()
    graph.add((EX.Enum, RDF.type, OWL.Class))
    graph.add((EX.First, RDF.type, OWL.Class))
    graph.add((EX.First, RDFS.subClassOf, EX.Enum))
    graph.add((EX.Second, RDF.type, OWL.Class))
    graph.add((EX.Second, RDFS.subClassOf, EX.Enum))
    overlay = Overlay(enum_root=str(EX.Enum))
    before = package(tmp_path, "before", graph, overlay=overlay)
    graph.set((EX.Second, RDFS.subClassOf, EX.First))
    after = package(tmp_path, "after", graph, overlay=overlay)
    path = after / "_support.json"
    support = json.loads(path.read_text())
    for record in support["constraints"]:
        if record["parameter"] == str(SH.maxCount):
            record["enforcement"] = ["validation"]
    path.write_text(json.dumps(support))
    changes = compare_packages(before, after).changes
    assert any(
        row.category == "enum"
        and row.target == str(EX.Second)
        and row.field == "parents"
        for row in changes
    )
    assert any(
        row.category == "support" and row.field == str(SH.maxCount) for row in changes
    )


def test_review_includes_named_individual_types(tmp_path):
    graph = source()
    graph.add((EX.Rover, RDF.type, EX.Dog))
    graph.add((EX.Owner, SH.property, EX.Favorite))
    graph.add((EX.Favorite, SH.path, EX.favorite))
    graph.add((EX.Favorite, SH["class"], EX.Animal))
    graph.add((EX.Favorite, SH.hasValue, EX.Rover))
    before = package(tmp_path, "before", graph)
    graph.set((EX.Rover, RDF.type, EX.Animal))
    after = package(tmp_path, "after", graph)
    assert any(
        row.category == "term" and row.target == str(EX.Rover) and row.field == "types"
        for row in compare_packages(before, after).changes
    )


def test_review_includes_quantity_projection_defaults(tmp_path):
    graph = Graph().parse(Path(__file__).parents[1] / "ontology/asm2d.ttl")
    before = package(tmp_path, "before", graph)
    volume = Namespace("https://watermetadata.org/plumb/asm2d#").AerobicVolumeShape
    prop = next(
        node
        for node in graph.objects(volume, SH.property)
        if graph.value(node, SH.path)
        == Namespace("http://data.ashrae.org/standard223#").hasValue
    )
    graph.set((prop, SH.defaultValue, Literal(1400.0)))
    after = package(tmp_path, "after", graph)
    assert any(
        row.category == "quantity"
        and row.target == str(volume)
        and row.field == "default"
        and row.after == 1400.0
        for row in compare_packages(before, after).changes
    )


def test_named_shapes_inside_validation_only_branches_are_fingerprinted(tmp_path):
    graph = source()
    head = BNode()
    tail = BNode()
    graph.add((EX.Owner, SH["or"], head))
    graph.add((head, RDF.first, EX.FirstBranch))
    graph.add((head, RDF.rest, tail))
    graph.add((tail, RDF.first, EX.SecondBranch))
    graph.add((tail, RDF.rest, RDF.nil))
    graph.add((EX.FirstBranch, SH.property, EX.Pattern))
    graph.add((EX.Pattern, SH.path, EX.code))
    graph.add((EX.Pattern, SH.pattern, Literal("old")))
    graph.add((EX.SecondBranch, SH.property, EX.CodeShape))
    before = package(tmp_path, "before", graph)
    graph.set((EX.Pattern, SH.pattern, Literal("new")))
    after = package(tmp_path, "after", graph)
    assert any(
        row.category == "support" and row.field == str(SH["or"])
        for row in compare_packages(before, after).changes
    )


def test_query_prefixes_include_bindings_without_ontology_version_noise(tmp_path):
    graph = source()
    query = BNode()
    graph.add((EX.Owner, SH.sparql, query))
    graph.add(
        (query, SH.select, Literal("SELECT $this WHERE { $this ex:blocked true }"))
    )
    graph.add((query, SH.prefixes, EX.ontology))
    graph.add((EX.ontology, SH.declare, EX.Prefix))
    graph.add((EX.Prefix, SH.prefix, Literal("ex")))
    graph.add((EX.Prefix, SH.namespace, Literal(str(EX))))
    before = package(tmp_path, "before", graph)
    graph.set((EX.ontology, OWL.versionInfo, Literal("2")))
    version = package(tmp_path, "version", graph)
    assert compare_packages(before, version).changes == ()
    graph.set((EX.Prefix, SH.namespace, Literal("urn:changed#")))
    after = package(tmp_path, "after", graph)
    assert any(
        row.category == "support" and row.field == str(SH.sparql)
        for row in compare_packages(version, after).changes
    )
