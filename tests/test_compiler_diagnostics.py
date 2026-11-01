"""Bindings and support boundaries are explicit, structured compiler results."""

import json

import pytest
from rdflib import BNode, Graph
from rdflib.namespace import SH

from plumb.gen import CompilationError, compile_modules, generate
from plumb.gen.overlays import Binding, Overlay
from plumb.cli import main
from plumb.gen.diagnostics import support_report
from plumb.gen.schema import extract
from plumb.gen.stable import stable_graph

SOURCE = """
@prefix ex: <urn:diagnostics#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<urn:diagnostics> a owl:Ontology .
ex:Equipment a owl:Class, sh:NodeShape ;
    sh:property ex:ColorShape .
ex:ColorShape sh:path ex:color ; sh:datatype xsd:string ;
    sh:minCount 1 ; sh:maxCount 1 ; sh:defaultValue "red" ; sh:in ("red" "green") ;
    sh:sparql [ sh:select "SELECT $this WHERE { FILTER(false) }" ] .
ex:feeds a owl:ObjectProperty ; rdfs:domain ex:Equipment ; rdfs:range ex:Equipment .
"""


def test_missing_required_bindings_produce_structured_errors_and_no_output(tmp_path):
    graph = Graph().parse(data=SOURCE, format="turtle")
    out = tmp_path / "package"
    out.mkdir()
    (out / "__init__.py").write_text("preserve existing output")
    with pytest.raises(CompilationError) as caught:
        generate(
            graph,
            out,
            name="Required",
            overlay=Overlay(
                rshift={"Missing": "feeds"},
                sensor_classes={"urn:kind": "Absent"},
            ),
        )
    assert {record["kind"] for record in caught.value.diagnostics} == {
        "rshift",
        "sensor-class",
    }
    assert all(
        record["required"] and record["status"] == "missing"
        for record in caught.value.diagnostics
    )
    assert "Missing" in str(caught.value) and "Absent" in str(caught.value)
    assert (out / "__init__.py").read_text() == "preserve existing output"
    assert not (out / "_support.json").exists()


def test_optional_bindings_are_reported_instead_of_silently_skipped():
    graph = Graph().parse(data=SOURCE, format="turtle")
    output = compile_modules(
        graph,
        name="Optional",
        overlay=Overlay(
            rshift={Binding("Missing", required=False): "feeds"},
        ),
    )
    report = json.loads(output["_support.json"])
    (record,) = report["bindings"]
    assert record["status"] == "missing" and not record["required"]
    assert "Missing" in record["reason"]
    assert "# skipped" not in output["__init__.py"]


def test_iri_bindings_survive_class_and_property_alias_changes():
    graph = Graph().parse(
        data=SOURCE
        + """
        <urn:preferred#Equipment> a owl:Class .
        <urn:preferred#feeds> a owl:ObjectProperty ;
            rdfs:domain ex:Equipment ; rdfs:range ex:Equipment .
    """,
        format="turtle",
    )
    output = compile_modules(
        graph,
        name="Aliases",
        overlay=Overlay(
            primary_namespace="urn:preferred#",
            rshift={"urn:diagnostics#Equipment": "urn:diagnostics#feeds"},
        ),
    )
    assert "Equipment_2._RSHIFT = 'feeds_2'" in output["__init__.py"]
    (record,) = json.loads(output["_support.json"])["bindings"]
    assert record["status"] == "resolved"


def test_support_report_distinguishes_checks_and_validation_only_constraints():
    output = compile_modules(Graph().parse(data=SOURCE, format="turtle"), name="Report")
    records = json.loads(output["_support.json"])["constraints"]
    by_parameter = {
        record["parameter"].rsplit("#", 1)[-1]: record for record in records
    }
    assert by_parameter["minCount"]["enforcement"] == ["constructor", "validation"]
    assert by_parameter["maxCount"]["enforcement"] == ["runtime", "validation"]
    assert by_parameter["defaultValue"]["enforcement"] == ["constructor"]
    assert by_parameter["in"]["enforcement"] == ["runtime", "validation"]
    sparql = by_parameter["sparql"]
    assert sparql["enforcement"] == ["validation"]
    assert sparql["target"] == "urn:diagnostics#Equipment"
    assert sparql["source"] == "urn:diagnostics#ColorShape"
    assert sparql["path"] == "urn:diagnostics#color"
    assert "exact RDF datatype" in by_parameter["datatype"]["reason"]


def test_support_report_is_stable_when_equivalent_anonymous_sources_swap_labels():
    graph = stable_graph(
        Graph().parse(
            data=SOURCE
            + """
            ex:First a owl:Class ; sh:property [
                sh:path ex:status ;
                sh:sparql [ sh:select "SELECT $this WHERE { FILTER(false) }" ]
            ] .
            ex:Second a owl:Class ; sh:property [
                sh:path ex:status ;
                sh:sparql [ sh:select "SELECT $this WHERE { FILTER(false) }" ]
            ] .
            """,
            format="turtle",
        )
    )
    # These query nodes have identical content and anonymous incoming context.
    # Their numeric suffix assignment is interchangeable across interpreter runs.
    groups: dict[str, list[BNode]] = {}
    for node in graph.objects(None, SH.sparql):
        if isinstance(node, BNode):
            groups.setdefault(str(node).split("_")[0], []).append(node)
    (first, second) = next(nodes for nodes in groups.values() if len(nodes) == 2)
    swapped = {first: second, second: first}
    equivalent = Graph()
    for subject, predicate, value in graph:
        equivalent.add(
            (swapped.get(subject, subject), predicate, swapped.get(value, value))
        )
    classes = extract(graph, name="Sources").classes
    original = support_report(graph, classes)
    assert original == support_report(equivalent, classes)
    records = json.loads(original)["constraints"]
    scoped = [
        row
        for row in records
        if row["target"] in {"urn:diagnostics#First", "urn:diagnostics#Second"}
    ]
    assert len(scoped) == 2
    assert all(row["path"] == "urn:diagnostics#status" for row in scoped)


def test_unsupported_constructive_literal_fails_before_import(tmp_path):
    graph = Graph().parse(
        data=SOURCE.replace(
            'sh:defaultValue "red"', 'sh:defaultValue "red"@en'
        ).replace('sh:in ("red" "green")', 'sh:in ("red"@en "green"@en)'),
        format="turtle",
    )
    with pytest.raises(
        ValueError, match="urn:diagnostics#color.*language-tagged constructive literal"
    ):
        generate(graph, tmp_path / "unsupported", name="Unsupported")


@pytest.mark.parametrize("case", ["enum-root", "deferred-predicate", "class-predicate"])
def test_missing_semantic_adapter_targets_fail_explicitly(case):
    overlay = {
        "enum-root": Overlay(enum_root="urn:missing#Root"),
        "deferred-predicate": Overlay(deferred_properties=("urn:missing#endpoint",)),
        "class-predicate": Overlay(class_properties=("urn:missing#process",)),
    }[case]
    with pytest.raises(CompilationError, match="missing"):
        compile_modules(
            Graph().parse(data=SOURCE, format="turtle"), name="Missing", overlay=overlay
        )


def test_incompatible_optional_binding_is_an_error():
    with pytest.raises(CompilationError, match="collection of entity links") as caught:
        compile_modules(
            Graph().parse(data=SOURCE, format="turtle"),
            name="Invalid",
            overlay=Overlay(rshift={"Equipment": Binding("color", required=False)}),
        )
    assert caught.value.diagnostics[0]["status"] == "incompatible"


def test_cli_explains_compilation_errors_without_a_traceback(tmp_path, capsys):
    source = tmp_path / "schema.ttl"
    source.write_text(SOURCE)
    with pytest.raises(SystemExit) as caught:
        main(
            [
                "gen",
                "--file",
                str(source),
                "--name",
                "S223",
                "--out",
                str(tmp_path / "output"),
            ]
        )
    assert caught.value.code == 2
    error = capsys.readouterr().err
    assert "connector binding" in error and "Traceback" not in error
