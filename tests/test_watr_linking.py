"""The committed WaTr package links canonical S223 identities and typed views."""

import json
from pathlib import Path
import subprocess
import sys

import pytest
from rdflib import OWL, URIRef

from plumb import Model, connect, s223, watr
from plumb.core.validation import shapes_for
from plumb.gen.symbols import Symbols
from plumb.qudt import quantity_kinds, units


def test_every_shared_class_reuses_or_subclasses_its_canonical_definition():
    shared = s223.REGISTRY.by_iri.keys() & watr.REGISTRY.by_iri.keys()
    reused, views = [], []
    for iri in shared:
        original = s223.REGISTRY.by_iri[iri]
        selected = watr.REGISTRY.by_iri[iri]
        assert selected.meta.canonical is original
        assert issubclass(selected, original)
        (reused if selected is original else views).append(iri)
    assert reused and views
    assert watr.InletConnectionPoint is s223.InletConnectionPoint
    assert watr.Pipe is s223.Pipe
    assert (
        watr.QuantifiableObservableProperty.meta.canonical
        is s223.QuantifiableObservableProperty
    )
    assert issubclass(watr.Pump_2, s223.Pump)
    assert issubclass(watr.Pump_2, watr.Pump)
    assert not issubclass(watr.Pump, s223.Pump)


def test_exports_separate_new_identities_views_and_dependency_references():
    data = json.loads(Path(watr.__file__).with_name("_symbols.json").read_text())
    shared = s223.REGISTRY.by_iri.keys() & watr.REGISTRY.by_iri.keys()
    assert not shared.intersection(item["iri"] for item in data["classes"])
    assert {item["iri"] for item in data["views"]} <= shared
    assert not s223.REGISTRY.enums_by_iri.keys() & {
        item["iri"] for item in data["enums"]
    }
    (dependency,) = data["dependencies"]
    assert dependency["module"] == "plumb.s223"
    assert dependency["sha256"] == Symbols.load("plumb.s223").digest
    symbols = Symbols.load("plumb.watr")
    assert symbols.classes[s223.Pipe.meta.iri].python_module == "plumb.s223"
    assert symbols.classes[s223.Equipment.meta.iri].canonical_module == "plumb.s223"


@pytest.mark.parametrize("reverse", [False, True])
def test_mixed_properties_containment_enums_and_hydration(reverse):
    with Model("urn:linked-water#") as model:
        fan = s223.Fan("fan")
        extended = watr.QuantifiableObservableProperty(
            "extended-temperature",
            has_quantity_kind=quantity_kinds.Temperature,
            has_unit=units.DEG_C,
            has_value=20.0,
        )
        shared = s223.QuantifiableObservableProperty(
            "shared-temperature",
            has_quantity_kind=quantity_kinds.Temperature,
            has_unit=units.DEG_C,
            has_value=21.0,
        )
        tank = watr.Tank("tank", has_role=[watr.enums.values.Role_Backwash])
        fan.has_property.add(extended)
        tank.has_property.add(shared)
        canonical = s223.Equipment("canonical")
        water = watr.Equipment("water")
        canonical.contains(water)
        water.contains(tank)
        clarifier = watr.Clarifier("clarifier")
    assert list(clarifier.has_process) == [watr.Process_Settling]
    registries = [s223.REGISTRY, watr.REGISTRY]
    if reverse:
        registries.reverse()
    loaded = Model.from_graph(model.graph(), registries=registries)
    assert type(loaded["shared-temperature"]) is watr.QuantifiableObservableProperty
    assert (
        loaded["shared-temperature"].meta.canonical
        is s223.QuantifiableObservableProperty
    )
    assert list(getattr(loaded["fan"], "has_property")) == [
        loaded["extended-temperature"]
    ]
    assert list(getattr(loaded["tank"], "has_property")) == [
        loaded["shared-temperature"]
    ]
    assert list(getattr(loaded["canonical"], "contains_")) == [loaded["water"]]
    assert list(getattr(loaded["water"], "contains_")) == [loaded["tank"]]
    assert list(getattr(loaded["clarifier"], "has_process")) == [watr.Process_Settling]
    assert list(getattr(loaded["tank"], "has_role")) == [
        watr.enums.values.Role_Backwash
    ]
    # Automatic loading from owl:imports makes the same deterministic choice.
    automatic = Model.from_graph(model.graph())
    assert type(automatic["shared-temperature"]) is watr.QuantifiableObservableProperty


@pytest.mark.parametrize("reverse", [False, True])
def test_mixed_connections_select_water_policy_in_both_endpoint_orders(reverse):
    with Model("urn:linked-connections#") as model:
        canonical = s223.Equipment("canonical")
        water = watr.Tank("water")
        source, target = (water, canonical) if reverse else (canonical, water)
        handle = connect(source, target, medium=watr.enums.values.Fluid_Sludge)
        sensor = handle.sensor(
            "flow", kind=quantity_kinds.VolumeFlowRate, unit=units.M3_PER_SEC
        )
    assert isinstance(sensor, watr.FlowSensor)
    pipe = model.resolve().connection(handle)
    assert type(pipe) is s223.Pipe
    assert pipe.medium is watr.enums.values.Fluid_Sludge


def test_full_closure_covers_its_dependency_shape_bundle_once():
    graph = shapes_for([s223.Fan, watr.Tank], [s223.REGISTRY, watr.REGISTRY])
    schema = watr.REGISTRY.schema_graph
    assert schema is not None
    assert set(graph) == set(schema)


def test_canonical_port_requirements_are_not_duplicated_by_views():
    assert watr.Filter_2._classinfo.cp_slots == ()
    assert len(watr.Filter_2.meta.port_contract.slots) == len(
        s223.Filter.meta.port_contract.slots
    )


def test_shared_enums_are_identical_and_new_values_retain_canonical_parents():
    for iri, original in s223.REGISTRY.enums_by_iri.items():
        assert watr.REGISTRY.enums_by_iri[iri] is original
    sludge = watr.enums.values.Fluid_Sludge
    assert sludge.is_a(s223.enums.values.Mix_Fluid)
    assert sludge not in s223.enums.values.Mix_Fluid.descendants


def test_water_enum_on_canonical_entity_selects_its_vocabulary_shapes_and_import():
    with Model("urn:linked-enum#") as model:
        s223.Equipment("equipment", has_role=[watr.enums.values.Role_Backwash])
    assert model.validate(infer=False)
    graph = model.graph()
    assert (URIRef(model.ontology_iri), OWL.imports, URIRef(watr.ONTOLOGY.iri)) in graph
    assert (
        str(graph.value(URIRef(watr.ONTOLOGY.iri), OWL.versionInfo))
        == watr.ONTOLOGY.version
    )
    loaded = Model.from_graph(graph)
    assert type(loaded["equipment"]) is watr.Equipment


def test_water_medium_selects_policy_between_two_canonical_entities():
    with Model("urn:linked-medium#") as model:
        handle = connect(
            s223.Equipment("source"),
            s223.Equipment("target"),
            medium=watr.enums.values.Fluid_Sludge,
        )
        sensor = handle.sensor(
            "flow", kind=quantity_kinds.VolumeFlowRate, unit=units.M3_PER_SEC
        )
    assert isinstance(sensor, watr.FlowSensor)
    assert type(model.resolve().connection(handle)) is s223.Pipe


_STATE = """
def state(s):
    classes = []
    for iri, cls in sorted(s.REGISTRY.by_iri.items()):
        connector = cls._CONNECTOR
        classes.append((iri, cls.__module__, [(p.name, p.predicate, p.min_count, p.max_count) for p in cls.meta.properties],
                        connector.registry.ontology.iri if connector else None,
                        sorted(connector.connection_classes.items()) if connector else None))
    enums = [(iri, [c.iri for c in value.children], [p.iri for p in value.parents], [c.iri for c in value.constituents])
             for iri, value in sorted(s.REGISTRY.enums_by_iri.items())]
    return classes, enums
"""


@pytest.mark.parametrize("reverse", [False, True])
def test_import_orders_do_not_mutate_s223_metadata_or_enum_trees(reverse):
    baseline = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json; from plumb import s223\n"
            + _STATE
            + "\nprint(json.dumps(state(s223)))",
        ],
        capture_output=True,
        text=True,
    )
    imports = (
        "from plumb import watr, s223" if reverse else "from plumb import s223, watr"
    )
    linked = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json\n"
            + imports
            + "\n"
            + _STATE
            + "\nassert watr.REGISTRY._schema_graph is None\nprint(json.dumps(state(s223)))",
        ],
        capture_output=True,
        text=True,
    )
    assert baseline.returncode == linked.returncode == 0, (
        baseline.stderr + linked.stderr
    )
    assert json.loads(baseline.stdout) == json.loads(linked.stdout)


def test_mixed_authoring_signatures_accept_canonical_values_and_reject_unrelated_types(
    tmp_path,
):
    positive = tmp_path / "positive.py"
    positive.write_text("""
from plumb import s223, watr
from plumb.watr.drinking_water import RapidSandFiltrationStage

def link(fan: s223.Fan, tank: watr.Tank, sensor: watr.Sensor,
         stage: RapidSandFiltrationStage, shared: s223.QuantifiableObservableProperty,
         extended: watr.QuantifiableObservableProperty) -> s223.QuantifiableObservableProperty:
    fan.has_property.add(extended)
    tank.has_property.add(shared)
    stage.has_property.add(shared)
    sensor.has_measurement_range.add(shared)
    return extended
""")
    negative = tmp_path / "negative.py"
    negative.write_text("""
from plumb import s223, watr
def invalid(fan: s223.Fan, tank: watr.Tank) -> None:
    fan.has_property.add(tank)
""")
    checker = str(Path(sys.executable).with_name("ty"))
    good = subprocess.run(
        [checker, "check", str(positive)], capture_output=True, text=True
    )
    bad = subprocess.run(
        [checker, "check", str(negative)], capture_output=True, text=True
    )
    assert good.returncode == 0, good.stdout + good.stderr
    assert bad.returncode != 0 and "invalid-argument-type" in bad.stdout, (
        bad.stdout + bad.stderr
    )
