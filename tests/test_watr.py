"""WaTr reuses the S223 authoring and deferred-resolution machinery."""

import pytest
from rdflib import URIRef
from typing import Any, cast

from plumb import Model, connect
from plumb import s223, watr
from plumb.core.errors import RangeError
from plumb.qudt import QuantityAmount as Q, quantity_kinds, units
from plumb.watr import enums
from plumb.watr.drinking_water import RapidSandFiltrationStage

W = "https://watermetadata.org/ontology/watr#"


@pytest.fixture
def m():
    with Model("urn:example/water#") as model:
        yield model


def test_extension_terms_keep_public_names():
    assert watr.ONTOLOGY.iri == "https://watermetadata.org/ontology/watr"
    assert watr.Pump.meta.iri == "https://watermetadata.org/ontology/watr#Pump"
    assert watr.Pump_2.meta.iri == "http://data.ashrae.org/standard223#Pump"
    # WaTr 0.3 pumps accept any Mix-Fluid (e.g. sludge), so they extend
    # s223:Equipment rather than s223:Pump, which admits only water, oil, or
    # refrigerant.
    assert not issubclass(watr.Pump, watr.Pump_2)
    assert issubclass(watr.Pump, watr.Equipment)


def test_shared_ontology_ranges_work_across_package_boundaries(m):
    # Both generated signatures and runtime checks accept canonical types.
    fan = s223.Fan("s223-fan")
    property_ = watr.QuantifiableObservableProperty(
        "watr-temperature", has_quantity_kind=quantity_kinds.Temperature
    )
    fan.has_property.add(property_)
    assert property_ in fan.has_property
    assert property_.meta.is_a(s223.Property)
    tank = watr.Tank("watr-tank")
    other = s223.QuantifiableObservableProperty(
        "s223-temperature", has_quantity_kind=quantity_kinds.Temperature
    )
    tank.has_property.add(other)
    assert other in tank.has_property
    with pytest.raises(RangeError):
        cast(Any, fan.has_property).add(tank)


def test_latest_watr_terms_are_available():
    assert watr.MediaFiltrationUnit.meta.iri.endswith("#MediaFiltrationUnit")
    assert issubclass(watr.BeltFilterPress, watr.DewateringUnit)
    assert issubclass(watr.Process_ThermalHydrolysis, watr.Process_Hydrolysis)
    assert enums.values.ReducingAgent.iri.endswith("#ReducingAgent")


def test_class_implied_process_and_objective_are_filled_in(m):
    # WaTr's ClassDefaultsRule infers these in RDF; the generated classes
    # apply the same defaults so the authored model already carries them.
    clarifier = watr.Clarifier("clarifier")
    assert list(clarifier.has_process) == [watr.Process_Settling]
    assert list(clarifier.has_treatment_objective) == [
        watr.TreatmentObjective_Clarification
    ]
    # Only the unconnected outlets remain; nothing about process or objective.
    messages = [issue.message for issue in m.validate(infer=False).violations]
    assert messages
    assert not [text for text in messages if "rocess" in text or "bjective" in text]


def test_direct_watr_connection_point_shapes_are_compiled():
    slots = watr.Reactor._classinfo.cp_slots
    assert {(slot.direction, slot.medium) for slot in slots} >= {
        ("in", "http://data.ashrae.org/standard223#Mix-Fluid"),
        ("out", "http://data.ashrae.org/standard223#Mix-Fluid"),
    }
    constraint = watr.Clarifier._classinfo.cp_constraints[0]
    assert constraint.operator == "and"


def test_watr_domains_prefer_coherent_medium_assignment(m):
    source = watr.Chiller("source")
    pump = watr.Pump("transfer-pump")
    tank = watr.Tank("product-tank")
    inlet = connect(source, pump)
    outlet = connect(pump, tank)

    assert m.check().complete
    resolved = m.resolve()
    inlet_pipe = resolved.connection(inlet)
    outlet_pipe = resolved.connection(outlet)

    assert isinstance(inlet_pipe, watr.Pipe)
    assert isinstance(outlet_pipe, watr.Pipe)
    assert inlet_pipe.medium is enums.values.Fluid_Water
    assert outlet_pipe.medium is enums.values.Fluid_Water
    assert list(pump.has_connection_point) == []
    assert len(list(resolved[pump.name].has_connection_point)) == 2


def test_broad_watr_fluid_domain_can_be_narrowed_explicitly(m):
    source = watr.Tank("source")
    target = watr.Tank("target")
    handle = connect(source, target, medium=enums.values.Fluid_Sludge)

    connection = m.resolve().connection(handle)
    assert isinstance(connection, watr.Pipe)
    assert connection.medium is enums.values.Fluid_Sludge


def test_one_sided_shapes_leave_other_directions_open(m):
    # Clarifier's shapes require only outlets; SHACL leaves inlets open, so a
    # plain connect() into it gets a generic inlet beside the required outlets.
    clarifier = watr.Clarifier("clarifier")
    handle = connect(watr.Tank("source"), clarifier, medium=enums.values.Fluid_Water)

    resolved = m.resolve()
    assert resolved.explain(handle).target_point == "clarifier-in"
    points = list(resolved["clarifier"].has_connection_point)
    assert sum(isinstance(point, watr.InletConnectionPoint) for point in points) == 1
    assert sum(isinstance(point, watr.OutletConnectionPoint) for point in points) == 2


def test_shape_maximum_still_closes_one_sided_equipment():
    from plumb.watr import seawater_ro

    with Model("urn:example/feed#") as model:
        connect(
            watr.Tank("tank"),
            seawater_ro.SeawaterFeed("feed"),
            medium=enums.values.Fluid_Water,
        )
    report = model.check()
    assert report.status == "unsatisfiable"
    assert any(
        "shape maximum connection-point count" in label
        for issue in report.issues
        for label in issue.labels
    )


def test_watr_connection_handle_stages_role_with_collection_api(m):
    handle = connect(
        watr.Tank("filter"),
        watr.Tank("backwash"),
        medium=enums.values.Fluid_Water,
    )
    handle.has_role.add(enums.values.Role_Backwash)

    assert enums.values.Role_Backwash in handle.has_role
    assert m.resolve().connection(handle).has_role == [enums.values.Role_Backwash]


def test_named_paired_ports_propagate_medium_through_solver(m):
    source = watr.Chiller("source")
    exchanger = watr.PressureExchanger("pxr")
    target = watr.Tank("target")
    feed_in = exchanger.port("pxr-feed-in", direction="in")
    feed_out = exchanger.port("pxr-feed-out", direction="out")
    feed_in.pair(feed_out)

    inlet = connect(source, feed_in)
    outlet = connect(feed_out, target)

    resolved = m.resolve()
    assert resolved.connection(inlet).medium is enums.values.Fluid_Water
    assert resolved.connection(outlet).medium is enums.values.Fluid_Water
    resolved_in = resolved["pxr-feed-in"]
    resolved_out = resolved["pxr-feed-out"]
    assert resolved_in.paired_with is resolved_out
    assert resolved_out.paired_with is resolved_in


def test_resolution_explains_paired_port_medium_propagation(m):
    source = watr.Tank("source")
    exchanger = watr.PressureExchanger("pxr")
    feed_in = exchanger.port(
        "pxr-feed-in",
        direction="in",
        medium=enums.values.Fluid_Sludge,
    )
    feed_out = exchanger.port("pxr-feed-out", direction="out")
    feed_in.pair(feed_out)
    handle = connect(feed_out, source.port("source-in", direction="in"))

    explanation = m.resolve().explain(handle)

    assert explanation.medium is enums.values.Fluid_Sludge
    assert explanation.medium_reason == "paired port"
    assert "paired with pxr-feed-in" in explanation.evidence[-1]
    assert str(explanation) == (
        "pxr-feed-out--source-in: pxr-feed-out -> source-in\n"
        "  medium: Fluid-Sludge (paired port)\n"
        "  - selected OutletConnectionPoint pxr-feed-out\n"
        "  - selected InletConnectionPoint source-in\n"
        "  - pxr-feed-out is paired with pxr-feed-in, whose medium is Fluid-Sludge"
    )


def test_prefixes_follow_namespaces_not_entity_order():
    def bindings(first, second):
        with Model("urn:example/order#") as model:
            first(f"a-{first.__name__}")
            second(f"b-{second.__name__}")
        graph = model.graph()
        return {
            prefix: str(namespace)
            for prefix, namespace in graph.namespaces()
            if prefix in {"s223", "watr"}
        }

    # watr.Pump_2 is s223:Pump, generated into the WaTr package.
    expected = {
        "s223": "http://data.ashrae.org/standard223#",
        "watr": "https://watermetadata.org/ontology/watr#",
    }
    assert bindings(watr.Pump_2, watr.Tank) == expected
    assert bindings(watr.Tank, watr.Pump_2) == expected


def test_from_graph_inference_uses_bundled_package_rules(m):
    # The model file carries no rules; inference must read the generated
    # package's bundled shapes, as validate() does.
    watr.Clarifier("clarifier")
    graph = m.graph()
    for predicate in ("hasProcess", "hasTreatmentObjective"):
        graph.remove((None, URIRef(f"{W}{predicate}"), None))

    plain = Model.from_graph(graph, registries=watr.REGISTRY)["clarifier"]
    assert isinstance(plain, watr.Clarifier)
    assert not list(plain.has_process)

    inferred = Model.from_graph(graph, registries=watr.REGISTRY, infer=True)
    clarifier = inferred["clarifier"]
    assert isinstance(clarifier, watr.Clarifier)
    assert watr.Process_Settling in clarifier.has_process
    assert watr.TreatmentObjective_Clarification in clarifier.has_treatment_objective


def test_sensor_helper_picks_class_from_quantity_kind(m):
    intake = watr.Pump("intake")
    sand_filter = RapidSandFiltrationStage("filter")
    raw = connect(watr.Tank("reservoir"), intake, name="raw-water")
    connect(intake, sand_filter.inlet)

    flow = raw.sensor(
        "raw-flow",
        kind=quantity_kinds.VolumeFlowRate,
        unit=units.M3_PER_DAY,
        of_medium=enums.values.Fluid_Water,
    )
    turbidity = sand_filter.filtered_water.sensor(
        "filtered-turbidity", kind=quantity_kinds.Turbidity, unit=units.NTU
    )
    temperature = intake.sensor(
        "intake-temperature",
        kind=quantity_kinds.Temperature,
        value=Q(12.0, units.DEG_C),
    )

    assert isinstance(flow, watr.FlowSensor)
    assert isinstance(turbidity, watr.TurbidityMeter)
    assert isinstance(temperature, watr.TemperatureSensor)
    reading = flow.observes
    assert isinstance(reading, watr.QuantifiableObservableProperty)
    assert reading.name == "raw-flow-value"
    assert reading.has_value is None
    assert reading.of_medium is enums.values.Fluid_Water
    observed = temperature.observes
    assert observed is not None
    assert observed.has_value == 12.0

    resolved = m.resolve()
    assert resolved["raw-flow"].has_observation_location is resolved.connection(raw)
    assert resolved["filtered-turbidity"].has_observation_location.name == (
        "filter-filtered_water"
    )


def test_media_compatibility_follows_s223_constituent_rules():
    values = enums.values
    # Pure media: one must be the other or its descendant.
    assert values.Fluid_Air.compatible_with(values.Mix_Fluid)
    # Mixtures sharing a constituent (H2O) are compatible, even sludge and water.
    assert values.Fluid_Water.compatible_with(values.Water_Freshwater)
    assert values.Fluid_Water.compatible_with(values.Fluid_Sludge)
    assert values.Water_Seawater.compatible_with(values.Water_Brine)
    # A mixture and a pure medium need a related constituent.
    assert not values.Fluid_Water.compatible_with(values.Fluid_Air)
    assert not values.Fluid_Water.compatible_with(values.Mix_Fluid)


def test_property_without_of_medium_takes_its_resolved_hosts_medium(m):
    chlorination = watr.ChlorinationUnit("contact")
    stage = RapidSandFiltrationStage("filter")
    clearwell = watr.Tank("clearwell")
    connect(stage.filtered_water, chlorination)
    finished = connect(chlorination, clearwell, name="finished")
    residual = finished.sensor(
        "chlorine-residual",
        kind=quantity_kinds.MassConcentration,
        unit=units.MilliGM_PER_L,
        of_substance=enums.values.Constituent_ChlorineResidual,
    )
    turbidity = stage.filtered_water.sensor(
        "filtered-turbidity", kind=quantity_kinds.Turbidity, unit=units.NTU
    )
    stated = finished.quantity(
        "finished-temperature",
        12.0,
        unit=units.DEG_C,
        kind=quantity_kinds.Temperature,
        of_medium=enums.values.Water_Freshwater,
    )

    # 223P requires ofMedium alongside ofSubstance; compile validates.
    resolved = m.compile()
    water = resolved.connection(finished).medium
    assert water is enums.values.Fluid_Water
    assert resolved["chlorine-residual-value"].of_medium is water
    assert resolved["filtered-turbidity-value"].of_medium is water
    # A stated medium is kept, and the authored model is not changed.
    assert resolved["finished-temperature"].of_medium is enums.values.Water_Freshwater
    assert isinstance(stated, watr.QuantifiableProperty)
    assert stated.of_medium is enums.values.Water_Freshwater
    for sensor in (residual, turbidity):
        assert isinstance(sensor, watr.Sensor)
        observed = sensor.observes
        assert isinstance(observed, watr.QuantifiableObservableProperty)
        assert observed.of_medium is None


def test_incompatible_of_medium_is_a_resolution_conflict(m):
    stage = RapidSandFiltrationStage("filter")
    clearwell = watr.Tank("clearwell")
    filtered = connect(stage.filtered_water, clearwell, name="filtered")
    temperature = filtered.quantity(
        "air-temperature",
        20.0,
        unit=units.DEG_C,
        kind=quantity_kinds.Temperature,
        of_medium=enums.values.Fluid_Air,
    )

    report = m.check()
    assert report.status == "unsatisfiable"
    assert any(
        "air-temperature: ofMedium Fluid-Air must be compatible" in label
        for issue in report.issues
        for label in issue.labels
    )

    assert isinstance(temperature, watr.QuantifiableProperty)
    temperature.of_medium = enums.values.Water_Freshwater
    assert m.check().complete


def test_sensor_helper_accepts_explicit_class_and_falls_back_to_sensor(m):
    tank = watr.Tank("clearwell")
    level = tank.sensor(
        "level",
        kind=quantity_kinds.Length,
        unit=units.M,
        sensor_class=watr.LevelSensor,
    )
    generic = tank.sensor(
        "density", kind=quantity_kinds.Density, unit=units.KiloGM_PER_M3
    )

    assert type(level) is watr.LevelSensor
    assert type(generic) is watr.Sensor
    with pytest.raises(TypeError, match="Sensor subclass"):
        tank.sensor(
            "bad",
            kind=quantity_kinds.Length,
            unit=units.M,
            sensor_class=watr.Pump,
        )
    with pytest.raises(ValueError, match="incompatible"):
        tank.sensor("bad", kind=quantity_kinds.Temperature, unit=units.M)
    with pytest.raises(TypeError, match="observation location"):
        observed = level.observes
        assert observed is not None
        observed.sensor("bad", kind=quantity_kinds.Length, unit=units.M)
    assert "bad" not in {entity.name for entity in m.entities}
