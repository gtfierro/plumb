"""Core snapshot ownership and domain dispatch, independent of ontology names."""

import pytest
import subprocess
import sys
from rdflib import BNode, Graph, Literal, RDF, URIRef
import toy

from plumb import Model, ModelingError


def test_plain_snapshot_copies_relationships_and_remains_stable_after_edits():
    with Model("urn:lifecycle#") as model:
        owner = toy.Equipment("owner")
        child = toy.Fan("child", rated_power=2.0)
        owner.has_part.add(child)
        owner.feeds.add(child)
    snapshot = model.resolve()
    assert snapshot["owner"] is not owner
    assert list(snapshot["owner"].has_part) == [snapshot["child"]]
    assert list(snapshot["child"].fed_by) == [snapshot["owner"]]
    assert model.resolve() is snapshot
    child.rated_power = 3.0
    owner.has_part.remove(child)
    assert snapshot["child"].rated_power == 2.0
    assert list(snapshot["owner"].has_part) == [snapshot["child"]]
    assert model.resolve() is not snapshot
    with pytest.raises(ModelingError, match="immutable"):
        snapshot["child"].rated_power = 4.0


def test_loaded_snapshot_preserves_foreign_iris_and_unprojected_rdf():
    graph = Graph()
    first, second = URIRef("urn:first#same"), URIRef("urn:second#same")
    unknown, predicate = BNode("unknown"), URIRef("urn:extra")
    graph.add((first, RDF.type, URIRef(toy.Equipment.meta.iri)))
    graph.add((second, RDF.type, URIRef(toy.Fan.meta.iri)))
    graph.add((first, URIRef("urn:toy#hasPart"), second))
    graph.add((unknown, predicate, Literal("preserved")))
    loaded = Model.from_graph(graph, registries=toy._REGISTRY, namespace="urn:loaded#")
    snapshot = loaded.resolve()
    assert {entity.meta.instance_iri for entity in snapshot} == {
        str(first),
        str(second),
    }
    assert set(snapshot.graph()) == set(graph)
    assert snapshot._model.resolve() is snapshot
    loaded["same"].label = "changed"
    graph.add((unknown, predicate, Literal("new")))
    assert snapshot["same"].label != "changed"
    assert (unknown, predicate, Literal("new")) not in snapshot.graph()
    returned = snapshot.graph()
    returned.remove((None, None, None))
    assert len(snapshot.graph()) > 0


def test_plain_models_do_not_import_the_connection_backend():
    script = """
import importlib.abc
import sys

class BlockBackend(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {'z3', 'plumb.solver223', 'plumb.domain223', 'plumb.topology223'}:
            raise AssertionError('plain RDF imported ' + fullname)

sys.meta_path.insert(0, BlockBackend())
sys.path.insert(0, 'tests')
import toy
from plumb import Model, brick, connect
for equipment in (toy.Equipment, brick.Equipment):
    with Model('urn:plain#') as model:
        a, b = equipment('a'), equipment('b')
        connect(a, b)
    assert model.check().complete
    resolved = model.compile(validate=False)
    assert len(resolved) == 2
    assert len(resolved.graph()) > 0
    assert list(resolved['a'].walk()) == []
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_sparse_plans_reuse_unaffected_components(monkeypatch):
    from plumb import connect, s223
    from plumb import solver223

    original = solver223._solve_component
    calls = []

    def solve(handles, **options):
        calls.append(tuple(handle.name for handle in handles))
        return original(handles, **options)

    monkeypatch.setattr(solver223, "_solve_component", solve)
    with Model("urn:cache#") as model:
        a = s223.Damper("a")
        first = connect(a, s223.Fan("b"))
        connect(s223.Damper("c"), s223.Fan("d"))
    assert model.check().complete
    assert len(calls) == 2
    before = model.resolve()
    assert len(calls) == 2
    a.label = "Renamed equipment"
    after = model.resolve()
    assert len(calls) == 2
    assert after["a"].label == "Renamed equipment"
    assert before["a"].label == "a"
    first.medium = s223.enums.values.Fluid_Air
    model.resolve()
    assert len(calls) == 3


def test_point_labels_invalidate_cached_interchangeability():
    from plumb import connect, s223

    with Model("urn:point-labels#") as model:
        terminal = s223.DualDuctTerminal("terminal")
        connect(s223.Damper("supply"), terminal)
    assert model.check().complete
    points = [
        point
        for point in terminal.has_connection_point
        if point.meta.is_a(s223.InletConnectionPoint)
    ]
    points[0].label = "Primary inlet"
    assert model.check().status == "underconstrained"


def test_failed_materialization_does_not_publish_or_change_authored_objects(
    monkeypatch,
):
    from plumb import connect, s223, solver223

    with Model("urn:failed-snapshot#") as model:
        connect(s223.Damper("damper"), s223.Fan("fan"))
    revision, entities = model._revision, tuple(model.entities)
    original = solver223._materialize

    def fail(build, plans):
        original(build, plans)
        raise RuntimeError("fail after domain objects were created")

    monkeypatch.setattr(solver223, "_materialize", fail)
    with pytest.raises(RuntimeError, match="fail after"):
        model.resolve()
    assert model._resolved_cache is None
    assert model._revision == revision and tuple(model.entities) == entities
    assert not any(entity.meta.is_a(s223.Connection) for entity in model)
    monkeypatch.setattr(solver223, "_materialize", original)
    assert model.resolve().source_revision == revision


def test_failed_constructor_restores_revision_cache_names_and_inverse_links():
    with Model("urn:constructor-transaction#") as model:
        existing = toy.Equipment("existing")
        snapshot = model.resolve()
        revision = model._revision
        with pytest.raises(ModelingError, match="no property"):
            toy.Fan(feeds=[existing], unknown="invalid")
        assert model._revision == revision
        assert model.resolve() is snapshot
        assert not list(existing.fed_by)
        assert toy.Fan().name == "fan_1"


def test_snapshots_reject_foreign_handles_even_when_identifiers_match():
    from plumb import connect, s223

    handles, snapshots = [], []
    for namespace in ("urn:first#", "urn:second#"):
        with Model(namespace) as model:
            handles.append(connect(s223.Damper("damper"), s223.Fan("fan")))
        snapshots.append(model.resolve())
    assert handles[0].identifier == handles[1].identifier
    with pytest.raises(KeyError, match="does not belong"):
        snapshots[0].connection(handles[1])
    with pytest.raises(KeyError, match="does not belong"):
        snapshots[0].explain(handles[1])


def test_snapshot_explanations_are_stable_after_parallel_connection_is_authored():
    from plumb import connect, s223

    with Model("urn:stable-explanations#") as model:
        damper, fan = s223.Damper("damper"), s223.Fan("fan")
        first = connect(damper, fan)
    snapshot = model.resolve()
    expected = snapshot.explain(damper, fan)
    connect(damper, fan, name="parallel", ports="new")
    assert snapshot.explain(damper, fan) == snapshot.explain(first) == expected
    with pytest.raises(AttributeError):
        setattr(snapshot, "source_revision", -1)


def test_loaded_connection_topology_and_snapshot_do_not_import_native_planner():
    script = """
import importlib.abc
import sys

class BlockPlanner(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {'z3', 'plumb.solver223'}:
            raise AssertionError('loaded RDF imported ' + fullname)

sys.meta_path.insert(0, BlockPlanner())
from rdflib import Graph
from plumb import Model, s223
graph = Graph().parse(data='''
@prefix ex: <urn:loaded#> .
@prefix s: <http://data.ashrae.org/standard223#> .
ex:a a s:Fan ; s:hasConnectionPoint ex:ao .
ex:b a s:Fan ; s:hasConnectionPoint ex:bi .
ex:ao a s:OutletConnectionPoint ; s:isConnectionPointOf ex:a ;
      s:connectsThrough ex:duct ; s:hasMedium s:Fluid-Air .
ex:bi a s:InletConnectionPoint ; s:isConnectionPointOf ex:b ;
      s:connectsThrough ex:duct ; s:hasMedium s:Fluid-Air .
ex:duct a s:Duct ; s:connectsAt ex:ao, ex:bi ; s:hasMedium s:Fluid-Air .
''', format='turtle')
model = Model.from_graph(graph, registries=s223.REGISTRY)
assert model.check().complete
snapshot = model.resolve()
assert set(snapshot.graph()) == set(graph)
assert snapshot['a'].find_next() is snapshot['b']
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
