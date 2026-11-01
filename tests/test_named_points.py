"""Named points and interchangeable groups compiled from portable SHACL."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import pytest
from rdflib import Graph, URIRef

from plumb import AmbiguousModelError, Model, connect
from plumb.core.errors import ModelingError
from plumb.gen import generate
from plumb.s223 import Chiller, Damper, Fan, OutletConnectionPoint, Pump, enums


@pytest.fixture
def domain(tmp_path):
    source = Path(__file__).with_name("fixtures") / "named_points.ttl"
    path = generate(Graph().parse(source), tmp_path / "domain", name="NamedPoints")
    spec = spec_from_file_location("test_named_points_domain", path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_group_connection_ignores_interchangeable_point_permutations(domain):
    with Model("urn:test:groups#") as model:
        pump = domain.GroupedPump("pump")
        handle = connect(Chiller("chiller"), pump.inlets)
    assert model.check().complete
    resolved = model.resolve()
    assert len(resolved.point(pump.inlets)) == 2
    assert resolved.explain(handle).target_point in {
        point.name for point in resolved.point(pump.inlets)
    }
    loaded = Model.from_graph(resolved.graph(), registries=pump.meta.registry)
    restored = getattr(loaded["pump"], "inlets")
    assert {ref.name for ref in restored} == {"inlets-1", "inlets-2"}
    assert set(loaded.graph()) == set(resolved.graph())


def test_distinct_same_medium_inlets_require_explicit_selection(domain):
    with Model("urn:test:branches#") as model:
        pump = domain.BranchedPump("pump")
        connect(Chiller("chiller"), pump)
    assert model.check().status == "underconstrained"
    with pytest.raises(AmbiguousModelError, match="ambiguous"):
        model.resolve()
    with Model("urn:test:selected#") as selected:
        pump = domain.BranchedPump("pump")
        handle = connect(Chiller("chiller"), pump.secondary)
    assert selected.resolve().explain(handle).target_point == "pump-secondary"


def test_unconnected_named_points_materialize_and_enforce_medium(domain):
    with Model("urn:test:orphan#") as model:
        pump = domain.GroupedPump("pump")
        with pytest.raises(ModelingError, match="medium is fixed"):
            pump.outlet.medium = enums.values.Fluid_Air
    resolved = model.resolve()
    assert isinstance(resolved.point(pump.outlet), OutletConnectionPoint)
    assert len(resolved["pump"].ports) == 3


def test_named_point_roles_survive_shared_class_emission(domain):
    from plumb.gen.symbols import Symbols

    symbols = Symbols.decode(
        Path(domain.__file__).with_name("_symbols.json").read_text(),
        module=domain.__name__,
    )
    symbol = symbols.classes[domain.BranchedPump.meta.iri]
    runtime = {
        (slot.name, slot.label, slot.min_count, slot.max_count)
        for slot in domain.BranchedPump._classinfo.cp_slots
    }
    assert {
        (slot.name, slot.label, slot.min_count, slot.max_count)
        for slot in symbol.cp_slots
    } == runtime
    assert {slot[0] for slot in runtime} >= {"primary", "secondary", "outlet"}


def test_group_connection_rejects_incompatible_medium(domain):
    with Model("urn:test:incompatible#") as model:
        pump = domain.GroupedPump("pump")
        connect(Fan("fan"), pump.inlets)
    assert model.check().status == "unsatisfiable"


def test_failed_configuration_construction_restores_reserved_names(domain):
    with Model("urn:test:rollback-points#") as model:
        original = Pump("pump-inlets-1")
        with pytest.raises(ModelingError, match="pump-inlets-1"):
            domain.GroupedPump("pump")
    assert model.entities == [original]
    assert model._port_intents == []
    assert model._reserved_names == set()


def test_hydration_rejects_missing_discriminating_point_facts(domain):
    with Model("urn:test:point-facts#") as model:
        pump = domain.BranchedPump("pump")
    graph = model.graph()
    primary = URIRef(model.namespace + "pump-primary")
    graph.remove((primary, URIRef("http://www.w3.org/2000/01/rdf-schema#label"), None))
    with pytest.raises(ModelingError, match="cannot identify named point"):
        Model.from_graph(graph, registries=pump.meta.registry)


def test_operator_connection_explanation_uses_authored_endpoints():
    with Model("urn:test:explanation#") as model:
        damper, fan = Damper("damper"), Fan("fan")
        damper >> fan
    explanation = model.resolve().explain(damper, fan)
    assert explanation.source_point == "damper-out"
    assert explanation.target_point == "fan-in"


def test_named_points_restore_semantic_subclasses_instead_of_python_names(domain):
    from plumb.core import ClassInfo, OntologyInfo, Registry
    from plumb.s223 import InletConnectionPoint, REGISTRY
    from rdflib import RDF

    custom = Registry(OntologyInfo("Custom points", "urn:custom-points"))
    custom.include(REGISTRY)

    class CustomInlet(InletConnectionPoint):
        _classinfo = ClassInfo("urn:custom-points#Inlet", custom.ontology, custom)

    with Model("urn:test:subclass-points#") as model:
        pump = domain.GroupedPump("pump")
    graph = model.graph()
    point = URIRef(model.namespace + "pump-inlets-1")
    graph.set((point, RDF.type, URIRef(CustomInlet.meta.iri)))
    loaded = Model.from_graph(graph, registries=[pump.meta.registry, custom])
    refs = getattr(loaded["pump"], "inlets")
    assert len(refs) == 2
    assert any(type(ref._port) is CustomInlet for ref in refs)


def test_loaded_partial_point_projection_is_copied_without_reinterpreting_it(domain):
    from rdflib import RDFS

    with Model("urn:test:partial-points#") as model:
        pump = domain.BranchedPump("pump")
    graph = model.graph()
    graph.remove((URIRef(model.namespace + "pump-primary"), RDFS.label, None))
    loaded = Model.from_graph(graph, registries=pump.meta.registry, strict=False)
    snapshot = loaded.resolve()
    assert set(snapshot.graph()) == set(graph)
    assert snapshot["pump"].secondary.owner is snapshot["pump"]
    assert snapshot["pump"].secondary._port is snapshot["pump-secondary"]
    assert snapshot["pump"].secondary is not getattr(loaded["pump"], "secondary")
