"""Core snapshot ownership and domain dispatch, independent of ontology names."""

import pytest
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
