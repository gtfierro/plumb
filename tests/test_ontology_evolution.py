"""Ontology updates change sources and regeneration, without runtime patches."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import SH

from plumb import Model, connect, s223, watr
from plumb.core.errors import RangeError
from plumb.gen import CompilationError, compile_modules, generate
from plumb.gen.overlays import Overlay
from plumb.gen.review import compare_packages
from plumb.gen.sources import SourceLock

EX = Namespace("urn:evolution#")
FIXTURES = Path(__file__).parent / "fixtures"


def load_package(path: Path, name: str, monkeypatch):
    spec = importlib.util.spec_from_file_location(name, path / "__init__.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def lock_source(root: Path, graph: Graph) -> SourceLock:
    """Model the maintainer's explicit source/manifest update, entirely offline."""
    source = root / "ontology.ttl"
    source.write_text(graph.serialize(format="turtle"))
    manifest = root / "sources.lock.json"
    manifest.write_text(
        json.dumps(
            {
                "format": 1,
                "graphs": {"example": ["upstream"]},
                "sources": {
                    "upstream": {
                        "path": source.name,
                        "identity": "urn:evolution#ontology",
                        "version": str(graph.value(EX.ontology, OWL.versionInfo)),
                        "kind": "document",
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    }
                },
            }
        )
    )
    return SourceLock(manifest)


def test_locked_source_update_drives_review_runtime_validation_and_typing(
    tmp_path, monkeypatch
):
    graph = Graph().parse(FIXTURES / "evolution.ttl")
    lock = lock_source(tmp_path, graph)
    baseline = tmp_path / "evolution_baseline"
    generate(lock.load("example"), baseline, name="Evolution")
    graph.set((EX.ontology, OWL.versionInfo, Literal("2")))
    graph.add((EX.Puppy, RDF.type, OWL.Class))
    graph.add((EX.Puppy, RDFS.subClassOf, EX.Dog))
    graph.set((EX.MemberShape, SH["class"], EX.Dog))
    graph.set((EX.MemberShape, SH.maxCount, Literal(1)))
    graph.set((EX.CodeShape, SH.defaultValue, Literal("new")))
    lock = lock_source(tmp_path, graph)
    candidate = tmp_path / "evolution_candidate"
    updated = lock.load("example")
    generate(updated, candidate, name="Evolution")
    report = compare_packages(baseline, candidate)
    assert {row.field for row in report.changes} >= {
        "range_groups",
        "max_count",
        "default_values",
    }
    assert any(
        row.category == "ontology" and row.field == "version"
        for row in report.provenance_changes
    )
    # Fresh parses, independent blank IDs, and reversed triple insertion must
    # preserve both the emitted bytes and the exact RDF meaning of the bundle.
    fresh = lock.load("example")
    reordered = Graph()
    for prefix, namespace in fresh.namespaces():
        reordered.bind(prefix, namespace)
    for triple in reversed(list(fresh)):
        reordered.add(triple)
    expected = compile_modules(updated, name="Evolution")
    assert expected == compile_modules(reordered, name="Evolution")
    bundled = Graph().parse(data=expected["_shapes.ttl"], format="turtle")
    assert isomorphic(bundled, fresh)
    api = load_package(candidate, "evolution_candidate", monkeypatch)
    with Model("urn:evolution:instance#") as model:
        puppy = api.Puppy("puppy")
        owner = api.Owner("owner", member=puppy)
        assert owner.code == "new"
        with pytest.raises(RangeError):
            owner.member = api.Animal("animal")
        assert owner.member is puppy
    assert model.validate(infer=False)
    graph = model.graph()
    loaded = Model.from_graph(graph, registries=api.REGISTRY)
    assert isomorphic(loaded.graph(), graph)
    assert getattr(loaded["owner"], "code") == "new"
    assert loaded.validate(infer=False)
    # RDF outside the new range is invalid even when it bypasses Python checks.
    invalid = Graph()
    invalid += graph
    invalid.set(
        (
            URIRef(owner.meta.instance_iri),
            EX.member,
            URIRef(model["animal"].meta.instance_iri),
        )
    )
    assert not Model.from_graph(invalid, registries=api.REGISTRY).validate(infer=False)
    positive = tmp_path / "positive.py"
    negative = tmp_path / "negative.py"
    positive.write_text(
        "from evolution_candidate import Owner, Puppy\nOwner('owner', member=Puppy('puppy'))\n"
    )
    negative.write_text(
        "from evolution_candidate import Owner, Animal\nOwner('owner', member=Animal('animal'))\n"
    )
    checker = str(Path(sys.executable).with_name("ty"))
    good = subprocess.run(
        [checker, "check", "--extra-search-path", str(tmp_path), str(positive)],
        capture_output=True,
        text=True,
    )
    bad = subprocess.run(
        [checker, "check", "--extra-search-path", str(tmp_path), str(negative)],
        capture_output=True,
        text=True,
    )
    assert good.returncode == 0, good.stdout + good.stderr
    assert bad.returncode != 0 and "invalid-argument-type" in bad.stdout, (
        bad.stdout + bad.stderr
    )


def test_named_water_port_evolution_preserves_mixed_models_and_hydration(
    tmp_path, monkeypatch
):
    graph = Graph().parse(FIXTURES / "named_points.ttl")
    baseline, candidate = tmp_path / "before", tmp_path / "after"
    generate(graph, baseline, name="WaterEvolution")
    water = Namespace("urn:test:named-points#")
    for prop in graph.objects(water.GroupedPumpShape, SH.property):
        if str(graph.value(prop, SH.name)) == "inlets":
            graph.set((prop, SH.qualifiedMinCount, Literal(3)))
            graph.set((prop, SH.qualifiedMaxCount, Literal(3)))
        if graph.value(prop, SH.minCount) is not None:
            graph.set((prop, SH.minCount, Literal(4)))
            graph.set((prop, SH.maxCount, Literal(4)))
    generate(graph, candidate, name="WaterEvolution")
    report = compare_packages(baseline, candidate)
    assert any(
        row.target == str(water.GroupedPump) and row.field == "named_points"
        for row in report.changes
    )
    assert any(
        row.field == "maximum_ports" and row.after == 4 for row in report.changes
    )
    api = load_package(candidate, "water_evolution", monkeypatch)
    with Model("urn:evolution:water#") as model:
        pump = api.GroupedPump("pump")
        source = s223.Chiller("source")
        tank = watr.Tank("tank")
        inlet = connect(source, pump.inlets)
        outlet = connect(pump.outlet, tank, medium=watr.enums.values.Fluid_Water)
    snapshot = model.resolve()
    assert len(snapshot.point(pump.inlets)) == 3
    assert len(snapshot["pump"].ports) == 4
    assert isinstance(snapshot.connection(inlet), s223.Pipe)
    assert isinstance(snapshot.connection(outlet), s223.Pipe)
    loaded = Model.from_graph(
        snapshot.graph(), registries=[api.REGISTRY, watr.REGISTRY]
    )
    assert len(getattr(loaded["pump"], "inlets")) == 3
    assert isomorphic(loaded.graph(), snapshot.graph())
    # Both front ends have the same byte and RDF determinism gates.
    fresh = Graph().parse(data=graph.serialize(format="turtle"), format="turtle")
    reversed_graph = Graph()
    for triple in reversed(list(fresh)):
        reversed_graph.add(triple)
    modules = compile_modules(graph, name="WaterEvolution")
    assert modules == compile_modules(reversed_graph, name="WaterEvolution")
    assert isomorphic(
        Graph().parse(data=modules["_shapes.ttl"], format="turtle"), graph
    )


def test_removed_required_adapter_target_names_adaptation_point_and_preserves_output(
    tmp_path,
):
    graph = Graph().parse(FIXTURES / "evolution.ttl")
    overlay = Overlay(rshift={str(EX.Owner): str(EX.member)})
    out = tmp_path / "package"
    generate(graph, out, name="Evolution", overlay=overlay)
    original = {path.name: path.read_bytes() for path in out.iterdir()}
    graph.remove((EX.Owner, None, None))
    with pytest.raises(CompilationError) as error:
        generate(graph, out, name="Evolution", overlay=overlay)
    (binding,) = error.value.diagnostics
    assert binding["kind"] == "rshift"
    assert binding["target"] == [str(EX.Owner), str(EX.member)]
    assert binding["required"] and binding["status"] == "missing"
    assert {path.name: path.read_bytes() for path in out.iterdir()} == original


def test_unsupported_constructive_update_names_source_constraint(tmp_path):
    graph = Graph().parse(FIXTURES / "evolution.ttl")
    graph.set((EX.CodeShape, SH.defaultValue, Literal("new", lang="en")))
    graph.remove((EX.CodeShape, SH["in"], None))
    with pytest.raises(
        ValueError, match="urn:evolution#code.*language-tagged constructive literal"
    ):
        generate(graph, tmp_path / "unsupported", name="Evolution")
