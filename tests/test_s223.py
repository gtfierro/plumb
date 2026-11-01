"""Integration tests against the committed generated 223P package."""

import pytest
from rdflib import RDF, URIRef

s223 = pytest.importorskip("plumb.s223")

from plumb import (  # noqa: E402
    AmbiguousModelError,
    Model,
    ModelingError,
    UnsatisfiableModelError,
    connect,
)
from plumb.core import RangeError  # noqa: E402
from plumb.qudt import quantity_kinds, units  # noqa: E402
from plumb.s223 import enums  # noqa: E402

S = "http://data.ashrae.org/standard223#"


@pytest.fixture
def m():
    with Model("urn:test/s223#") as model:
        yield model


# -- enums -----------------------------------------------------------------


def test_enum_hierarchy():
    assert enums.values.Fluid_Air.is_a(enums.values.Substance_Medium)
    assert enums.values.Water_ChilledWater.is_a(enums.values.Fluid_Water)
    assert not enums.values.Fluid_Air.is_a(enums.values.Fluid_Water)
    assert enums.values.Fluid_Air.iri == f"{S}Fluid-Air"


def test_enum_hierarchical_access():
    # Flat constants are primary; hierarchy access works for exploration.
    assert enums.values.Substance_Medium.Mix.Fluid.Air is enums.values.Fluid_Air


def test_generated_package_exposes_canonical_point_properties():
    with Model("urn:test/s223-names#"):
        fan = s223.Fan("fan")
        point = next(
            cp
            for cp in fan.has_connection_point
            if isinstance(cp, s223.InletConnectionPoint)
        )

    assert point.medium is enums.values.Fluid_Air
    assert point.owner is fan
    point.medium = enums.values.Fluid_Water
    assert point.medium is enums.values.Fluid_Water


def test_enum_tree_prints_all_descendants(capsys):
    result = enums.values.Substance_Medium.tree()

    assert result is None
    tree = capsys.readouterr().out
    assert tree.startswith("Substance-Medium\n├── Medium-Constituent\n")
    assert "│   ├── Constituent-H2O\n" in tree
    assert "├── Medium-Mix\n" in tree
    assert "│   ├── Mix-Fluid\n" in tree
    assert "│   │   ├── Fluid-Air\n" in tree
    assert tree.endswith("└── Medium-ThermalContact\n")


def test_enum_tree_text_options():
    tree = enums.values.Substance_Medium.tree_text(max_depth=1)
    assert "├── Medium-Constituent\n│   └── …" in tree
    assert "Fluid-Air" not in tree

    iris = enums.values.Fluid_Water.tree_text(max_depth=0, show_iris=True)
    assert iris.startswith(f"{S}Fluid-Water")
    assert "\n└── …" in iris

    with pytest.raises(ValueError, match="non-negative"):
        enums.values.Fluid_Water.tree_text(max_depth=-1)


def test_enums_registered():
    reg = s223.Connectable.meta.registry
    assert reg.resolve_enum(f"{S}Fluid-Water") is enums.values.Fluid_Water


# -- structure -------------------------------------------------------------


def test_scale_and_abstractness(m):
    assert len(s223.__all__) > 150
    assert s223.Connectable.meta.abstract
    with pytest.raises(ModelingError, match="organizational class"):
        s223.Connectable("x")
    assert issubclass(s223.Fan, s223.Equipment)


def test_connection_point_requires_medium(m):
    with pytest.raises(TypeError, match="medium"):
        s223.InletConnectionPoint("cp")


def test_fan_cp_slots_extracted():
    slots = {(s.direction, s.medium) for s in s223.Fan._classinfo.cp_slots}
    assert ("out", f"{S}Fluid-Air") in slots
    assert ("in", f"{S}Fluid-Air") in slots


# -- connection negotiation ------------------------------------------------


def test_rshift_negotiates_air_connection(m):
    damper = s223.Damper("oad")
    fan = s223.Fan("sf")
    result = damper >> fan
    assert result is fan

    resolved = m.resolve()
    duct = resolved["oad--sf"]
    assert isinstance(duct, s223.Duct)
    assert duct.medium is enums.values.Fluid_Air
    out_cp = resolved["oad-out"]
    in_cp = resolved["sf-in"]
    assert isinstance(out_cp, s223.OutletConnectionPoint)
    assert out_cp.medium is enums.values.Fluid_Air
    # full 223 plumbing, both directions, from one statement:
    resolved_damper = resolved[damper.name]
    resolved_fan = resolved[fan.name]
    assert out_cp in resolved_damper.has_connection_point
    assert out_cp.owner is resolved_damper
    assert out_cp.connection is duct
    assert out_cp in duct.connects_at
    assert in_cp in duct.connects_at
    assert in_cp.owner is resolved_fan


def test_connect_handle_resolves_connection_and_medium(m):
    handle = connect(s223.Chiller("ch"), s223.Pump("p"))
    conn = m.resolve().connection(handle)
    assert isinstance(conn, s223.Pipe)  # inferred from Fluid-Water
    assert conn.medium is enums.values.Fluid_Water  # chiller side constrains it


def test_boolean_layout_supplies_coil_connection_candidates(m):
    coil = s223.ChilledWaterCoil("coil")
    for name, cls, medium in (
        ("coil-air-in", s223.InletConnectionPoint, enums.values.Fluid_Air),
        ("coil-water-in", s223.InletConnectionPoint, enums.values.Fluid_Water),
        ("coil-air-out", s223.OutletConnectionPoint, enums.values.Fluid_Air),
        ("coil-water-out", s223.OutletConnectionPoint, enums.values.Fluid_Water),
    ):
        cls(name, medium=medium, owner=coil)
    handle = connect(s223.Chiller("ch"), coil)
    conn = m.resolve().connection(handle)

    assert isinstance(conn, s223.Pipe)
    assert conn.medium is enums.values.Fluid_Water
    inlet = m.resolve()["coil-water-in"]
    assert isinstance(inlet, s223.InletConnectionPoint)
    assert inlet.medium is enums.values.Fluid_Water


def test_incomplete_coil_layout_is_deferred_as_ambiguous(m):
    pump = s223.Pump("pump")
    connect(s223.Chiller("ch"), pump)
    connect(pump, s223.ChilledWaterCoil("coil"))

    assert m.check().status == "underconstrained"
    with pytest.raises(AmbiguousModelError):
        m.resolve()


def test_chaining_reads_along_the_flow(m):
    s223.Damper("oad") >> s223.Fan("sf") >> s223.Damper("ret")
    resolved = m.resolve()
    assert isinstance(resolved["oad--sf"], s223.Duct)
    assert isinstance(resolved["sf--ret"], s223.Duct)


def test_explicit_medium_and_connection_class(m):
    a, b = s223.Pump("a"), s223.Pump("b")
    handle = connect(a, b, medium=enums.values.Water_ChilledWater)
    conn = m.resolve().connection(handle)
    assert conn.medium is enums.values.Water_ChilledWater
    assert isinstance(conn, s223.Pipe)  # ChilledWater is_a Fluid-Water


def test_medium_affinity_is_a_preference_not_hard_preservation(m):
    source = s223.Chiller("water-source")
    pump = s223.Pump("pump")
    oil_side = s223.Pump("oil-side")
    s223.InletConnectionPoint(
        "oil-in",
        medium=enums.values.Fluid_Oil,
        owner=oil_side,
    )
    water = connect(source, pump)
    oil = connect(pump, oil_side)

    assert m.check().complete
    resolved = m.resolve()
    assert resolved.connection(water).medium is enums.values.Fluid_Water
    assert resolved.connection(oil).medium is enums.values.Fluid_Oil
    assert {cp.medium for cp in resolved[pump.name].has_connection_point} == {
        enums.values.Fluid_Water,
        enums.values.Fluid_Oil,
    }


def test_unconstrained_sides_remain_deferred(m):
    connect(s223.Pump("p1"), s223.Pump("p2"))
    assert m.check().status == "underconstrained"
    with pytest.raises(AmbiguousModelError):
        m.resolve()


def test_mutually_required_cycle_is_constructible(m):
    # 223 deadlock case: Junction requires a ConnectionPoint, which requires
    # its Connectable. The compiler demotes the container side to
    # validate-time, so a Junction is constructible and connectable.
    j = s223.Junction("j1", medium=enums.values.Fluid_Water)
    handle = connect(s223.Chiller("ch"), j)
    conn = m.resolve().connection(handle)
    assert conn.medium is enums.values.Fluid_Water


def test_incompatible_media_rejected(m):
    boiler = s223.Boiler("b")  # water outlet
    fan = s223.Fan("f")  # air inlet
    boiler >> fan
    assert m.check().status == "unsatisfiable"
    with pytest.raises(UnsatisfiableModelError):
        m.resolve()


def test_unbounded_slot_supports_multiple_connections(m):
    ch = s223.Chiller("ch")
    first = connect(ch, s223.Pump("p1"))
    second = connect(ch, s223.Pump("p2"))
    resolved = m.resolve()
    assert isinstance(resolved.connection(first), s223.Pipe)
    assert isinstance(resolved.connection(second), s223.Pipe)


def test_new_ports_are_allocated_on_bare_equipment(m):
    ch, pump = s223.Chiller("ch"), s223.Pump("p")
    first = connect(ch, pump, ports="new", medium=enums.values.Fluid_Water)
    second = connect(ch, s223.Pump("q"), ports="new")
    assert first.source.name == "ch-out"
    assert first.target.name == "p-in"
    assert second.source.name == "ch-out-2"
    assert {port.name for port in ch.ports} >= {"ch-out", "ch-out-2"}
    assert first.source.medium is enums.values.Fluid_Water
    resolved = m.resolve()
    assert isinstance(resolved.connection(first), s223.Pipe)


def test_new_ports_require_one_model(m):
    with Model("urn:test/other#"):
        other = s223.Pump("p")
    with pytest.raises(ModelingError, match="same Model"):
        connect(s223.Chiller("ch"), other, ports="new")
    assert not m._port_intents


def test_new_ports_are_refused_on_graph_backed_model(m):
    connect(s223.Chiller("ch"), s223.Pump("p"))
    loaded = Model.from_graph(m.resolve().graph(), registries=s223.REGISTRY)
    with pytest.raises(ModelingError, match="deferred S223/WaTr connections"):
        connect(loaded["ch"], loaded["p"], ports="new")
    assert not loaded._port_intents


def test_equipment_medium_accepts_enum_values(m):
    pump = s223.Pump("p", medium=[enums.values.Fluid_Water])
    assert pump.medium == [enums.values.Fluid_Water]
    assert (
        URIRef(m.namespace + "p"),
        URIRef(f"{S}hasMedium"),
        URIRef(f"{S}Fluid-Water"),
    ) in m.graph()


def test_single_value_for_collection_names_the_fix(m):
    with pytest.raises(RangeError, match=r"takes a collection.*pass \["):
        s223.Pump("p", medium=enums.values.Fluid_Water)
    assert "p" not in {entity.name for entity in m.entities}


def test_explain_by_equipment_finds_connection_through_concrete_point(m):
    pump, chiller = s223.Pump("p"), s223.Chiller("ch")
    inlet = s223.InletConnectionPoint(
        "ch-in", medium=enums.values.Fluid_Water, owner=chiller
    )
    connect(pump, inlet)
    resolved = m.resolve()
    # The solver treats the point's owner as the endpoint; so does explain().
    assert resolved.explain(pump, chiller).connection == "p--ch-in"
    assert resolved.explain(pump, inlet).connection == "p--ch-in"


def test_enum_collection_is_live_and_validated(m):
    pump = s223.Pump("p", medium=[enums.values.Fluid_Water])
    revision = m._revision
    pump.medium.add(enums.values.Fluid_Water, enums.values.Fluid_Air)
    assert pump.medium == [enums.values.Fluid_Water, enums.values.Fluid_Air]
    assert m._revision != revision  # cached resolution is invalidated
    with pytest.raises(RangeError):
        pump.medium.add("water")
    pump.medium.remove(enums.values.Fluid_Air)
    assert list(pump.medium) == [enums.values.Fluid_Water]
    assert enums.values.Fluid_Water in pump.medium
    pump.medium.clear()
    assert len(pump.medium) == 0
    assert not hasattr(pump.medium, "append")  # no unchecked list mutation


def test_resolved_enum_collection_is_immutable(m):
    pump = s223.Pump("p", has_role=[enums.values.Role_Supply])
    snapshot = m.resolve()
    with pytest.raises(ModelingError):
        snapshot[pump.name].has_role.add(enums.values.Role_Return)
    assert pump.has_role == [enums.values.Role_Supply]


def test_construction_materializes_required_cps(m):
    # The Fan shape requires an air inlet and outlet: they exist immediately.
    fan = s223.Fan("f")
    cps = list(fan.has_connection_point)
    assert len(cps) == 2
    assert {type(cp).__name__ for cp in cps} == {
        "InletConnectionPoint",
        "OutletConnectionPoint",
    }
    assert all(cp.medium is enums.values.Fluid_Air for cp in cps)


def test_existing_cps_reused_not_duplicated(m):
    fan = s223.Fan("f")
    handle = connect(fan, s223.Damper("d"))
    # negotiation binds the construction-time CPs; nothing extra appears
    assert len(list(fan.has_connection_point)) == 2
    resolved = m.resolve()
    assert resolved["f-out"].connection is resolved.connection(handle)
    assert m["f-out"].connection is None


def test_handle_assignments_transfer_to_frozen_snapshot(m):
    handle = connect(s223.Damper("d"), s223.Fan("f"))
    handle.label = "Supply duct"
    handle.comment = "authored before resolution"
    handle.has_role.add(enums.values.Role_Supply, enums.values.Role_Return)
    handle.has_role.remove(enums.values.Role_Return)

    resolved = m.resolve()
    duct = resolved.connection(handle)
    assert duct.label == "Supply duct"
    assert duct.comment == "authored before resolution"
    assert duct.has_role == [enums.values.Role_Supply]
    with pytest.raises(ModelingError, match="immutable"):
        duct.label = "changed"


def test_handle_collection_assignment_invalidates_resolution(m):
    handle = connect(s223.Damper("d"), s223.Fan("f"))
    handle.has_role.add(enums.values.Role_Supply)
    first = m.resolve()

    handle.has_role = [enums.values.Role_Return]
    second = m.resolve()
    assert second is not first
    assert list(handle.has_role) == [enums.values.Role_Return]
    assert second.connection(handle).has_role == [enums.values.Role_Return]

    with pytest.raises(TypeError, match="multi-valued"):
        handle.has_role = enums.values.Role_Supply


def test_resolution_cache_invalidates_on_handle_edit(m):
    handle = connect(s223.Damper("d"), s223.Fan("f"))
    first = m.resolve()
    assert m.resolve() is first

    handle.label = "Changed before recompilation"
    second = m.resolve()
    assert second is not first
    assert second.connection(handle).label == "Changed before recompilation"


def test_unsat_core_uses_authored_connection_name(m):
    connect(s223.Boiler("boiler"), s223.Fan("fan"))
    with pytest.raises(UnsatisfiableModelError) as caught:
        m.resolve()
    assert any("boiler--fan" in label for label in caught.value.core)
    # The message names the conflicting constraints, not just "inconsistent".
    assert all(label in str(caught.value) for label in caught.value.core)


def test_same_class_slots_with_different_media_each_get_a_point(m):
    # An IceMaker needs an electricity inlet and a water inlet: two inlets,
    # not the larger of the two slot counts.
    ice = s223.IceMaker("ice")
    handle = connect(s223.Equipment("supply"), ice, medium=enums.values.Fluid_Water)

    resolved = m.resolve()
    assert resolved.connection(handle).medium is enums.values.Fluid_Water
    inlets = [
        point
        for point in resolved["ice"].has_connection_point
        if isinstance(point, s223.InletConnectionPoint)
    ]
    assert {point.medium for point in inlets} == {
        enums.values.Fluid_Water,
        enums.values.Constituent_Electricity,
    }


def test_shape_maximum_of_zero_forbids_points_without_requiring_one(m):
    # 223P: "An AirHeatExchanger shall have no bidirectional connection points."
    exchanger = s223.AirHeatExchanger("hx")
    connect(s223.Damper("supply"), exchanger)

    assert m.check().status != "unsatisfiable"
    resolved = m.resolve()
    assert not [
        point
        for point in resolved["hx"].has_connection_point
        if isinstance(point, s223.BidirectionalConnectionPoint)
    ]


def test_identical_shape_points_are_interchangeable_and_named_by_owner(m):
    # A DualDuctTerminal needs two air inlets. The constructor makes both;
    # either can take the connection, so the choice is not an ambiguity.
    first = s223.DualDuctTerminal("ddt1")
    s223.DualDuctTerminal("ddt2")
    assert sorted(point.name for point in first.has_connection_point) == [
        "ddt1-in",
        "ddt1-in-2",
        "ddt1-out",
    ]
    connect(s223.Damper("supply"), first)

    assert m.check().complete
    m.resolve()


def test_explicit_port_medium_overrides_class_medium_domain(m):
    # Fan inlets must carry air, but a declared power inlet may carry
    # electricity; plain connections still infer air.
    fan = s223.Fan("fan")
    power = fan.port("fan-power", direction="in", medium=enums.values.Electricity_AC)
    supply = connect(s223.Equipment("panel"), power)
    air = connect(s223.Damper("damper"), fan)

    resolved = m.resolve()
    assert resolved.connection(supply).medium is enums.values.Electricity_AC
    assert resolved.explain(supply).medium_reason == "explicit port"
    assert resolved.connection(air).medium is enums.values.Fluid_Air


def test_medium_domain_conflict_is_named_in_unsat_core(m):
    connect(s223.Boiler("boiler"), s223.Fan("fan"))
    with pytest.raises(UnsatisfiableModelError) as caught:
        m.resolve()
    assert caught.value.core
    assert "fan-in: medium Fluid-Air" in caught.value.core


def _observed(subject):
    return subject.quantity(
        "reading",
        20.0,
        unit=units.DEG_C,
        kind=quantity_kinds.Temperature,
        capability="observable",
    )


def test_sensor_location_may_be_a_deferred_connection_or_port(m):
    fan = s223.Fan("fan")
    duct = connect(s223.Damper("damper"), fan, name="supply-duct")
    outlet = fan.port("fan-discharge", direction="out")
    at_duct = s223.TemperatureSensor(
        "duct-temp", has_observation_location=duct, observes=_observed(duct)
    )
    s223.TemperatureSensor(
        "discharge-temp",
        has_observation_location=outlet,
        observes=fan.quantity(
            "discharge",
            20.0,
            unit=units.DEG_C,
            kind=quantity_kinds.Temperature,
            capability="observable",
        ),
    )
    assert at_duct.has_observation_location is duct

    resolved = m.resolve()
    assert resolved["duct-temp"].has_observation_location is resolved.connection(duct)
    discharge = resolved["discharge-temp"].has_observation_location
    assert isinstance(discharge, s223.OutletConnectionPoint)
    assert discharge.name == "fan-discharge"
    graph = m.graph()
    location = URIRef("http://data.ashrae.org/standard223#hasObservationLocation")
    assert set(graph.objects(URIRef(m.namespace + "duct-temp"), location)) == {
        URIRef(m.namespace + "supply-duct")
    }


def test_changing_a_deferred_sensor_location_invalidates_resolution(m):
    fan = s223.Fan("fan")
    first = connect(s223.Damper("damper"), fan, name="first")
    sensor = s223.TemperatureSensor(
        "temp", has_observation_location=first, observes=_observed(first)
    )
    assert m.resolve()["temp"].has_observation_location.name == "first"
    outlet = fan.port("fan-discharge", direction="out")
    sensor.has_observation_location = outlet
    assert m.resolve()["temp"].has_observation_location.name == "fan-discharge"


def test_deferred_locations_are_limited_to_location_properties(m):
    fan = s223.Fan("fan")
    duct = connect(s223.Damper("damper"), fan)
    with pytest.raises(RangeError, match="links entities"):
        s223.TemperatureSensor(
            "temp",
            has_observation_location=fan,
            observes=duct,
        )
    with Model("urn:test:other#"):
        other = connect(s223.Damper("d2"), s223.Fan("f2"))
    with pytest.raises(RangeError, match="another Model"):
        s223.TemperatureSensor(
            "temp", has_observation_location=other, observes=_observed(duct)
        )


def test_actuator_commands_equipment_with_a_quantity_or_enumeration(m):
    fan = s223.Fan("fan")
    speed = fan.actuator("fan-speed", kind=quantity_kinds.Frequency, unit=units.HZ)
    start = fan.actuator(
        "fan-start", kind=enums.values.Binary_OnOff, value=enums.values.OnOff_Off
    )

    assert isinstance(speed, s223.Actuator)
    assert list(speed.actuates) == [fan]
    [speed_command] = speed.actuated_by_property
    assert isinstance(speed_command, s223.QuantifiableActuatableProperty)
    assert speed_command.name == "fan-speed-command"
    assert speed_command.has_value is None
    [start_command] = start.actuated_by_property
    assert isinstance(start_command, s223.EnumeratedActuatableProperty)
    assert start_command.has_enumeration_kind is enums.values.Binary_OnOff
    assert start_command.has_value is enums.values.OnOff_Off
    assert list(fan.actuated_by_property) == [speed_command, start_command]
    assert {prop.name for prop in fan.has_property} >= {
        "fan-speed-command",
        "fan-start-command",
    }
    assert m.validate().ok


def test_actuator_rejects_mismatched_kinds_and_non_equipment(m):
    fan = s223.Fan("fan")
    with pytest.raises(TypeError, match="takes no unit"):
        fan.actuator("bad", kind=enums.values.Binary_OnOff, unit=units.HZ)
    with pytest.raises(ValueError, match="member of"):
        fan.actuator(
            "bad", kind=enums.values.Binary_OnOff, value=enums.values.Binary_OnOff
        )
    with pytest.raises(TypeError, match="takes a number"):
        fan.actuator(
            "bad",
            kind=quantity_kinds.Frequency,
            unit=units.HZ,
            value=enums.values.OnOff_On,
        )
    # A Sensor is Equipment and may be actuated; its observed property is not.
    reading = fan.sensor(
        "fan-temperature", kind=quantity_kinds.Temperature, unit=units.DEG_C
    ).observes
    assert reading is not None
    with pytest.raises(TypeError, match="not Equipment"):
        reading.actuator("bad", kind=quantity_kinds.Frequency, unit=units.HZ)
    assert not {"bad", "bad-command"} & {entity.name for entity in m.entities}


def test_sensor_observes_an_enumerated_state(m):
    fan = s223.Fan("fan")
    status = fan.sensor("fan-status", kind=enums.values.Binary_OnOff)

    assert type(status) is s223.Sensor
    observed = status.observes
    assert isinstance(observed, s223.EnumeratedObservableProperty)
    assert observed.has_enumeration_kind is enums.values.Binary_OnOff


def test_sparse_components_resolve_independently():
    with Model("urn:test/sparse#") as model:
        handles = [connect(s223.Damper(f"d{i}"), s223.Fan(f"f{i}")) for i in range(30)]
    assert model.check().status == "complete"
    resolved = model.resolve()
    assert all(isinstance(resolved.connection(h), s223.Duct) for h in handles)


# -- containment -----------------------------------------------------------


def test_containment_negotiation(m):
    with s223.PhysicalSpace("building") as b:
        with s223.PhysicalSpace("room") as r:
            zone = s223.DomainSpace("zone", has_domain=enums.values.Domain_HVAC)
            ahu = s223.Fan("fan")
    # s223:contains is exposed as `contains_` (contains() is the method)
    assert r in b.contains_
    assert zone in r.encloses
    assert r in ahu.has_physical_location


# -- serialization ---------------------------------------------------------


def test_serialization_produces_223_triples(m):
    s223.Damper("oad") >> s223.Fan("sf")
    g = m.graph()
    ns = "urn:test/s223#"

    def u(x):
        return URIRef(ns + x)

    assert (u("oad--sf"), RDF.type, URIRef(f"{S}Duct")) in g
    assert (u("oad--sf"), URIRef(f"{S}hasMedium"), URIRef(f"{S}Fluid-Air")) in g
    assert (u("oad"), URIRef(f"{S}hasConnectionPoint"), u("oad-out")) in g
    assert (u("oad-out"), URIRef(f"{S}connectsThrough"), u("oad--sf")) in g
    assert (u("oad--sf"), URIRef(f"{S}connectsAt"), u("sf-in")) in g
    assert (u("sf-in"), URIRef(f"{S}hasMedium"), URIRef(f"{S}Fluid-Air")) in g


def test_cp_cannot_belong_to_two_connectables(m):
    f1, f2 = s223.Fan("f1"), s223.Fan("f2")
    cp = s223.OutletConnectionPoint("cp", medium=enums.values.Fluid_Air, owner=f1)
    with pytest.raises(ModelingError, match="already"):
        f2.has_connection_point.add(cp)


# -- validation & example --------------------------------------------------


def test_negotiated_model_conforms_to_223(m):
    """The whole point: what the negotiator emits passes 223's own shapes.

    Uses the package's recorded ontology source (a URL), so this needs the
    network; skipped when offline.
    """
    s223.Damper("oad") >> s223.Fan("sf")
    try:
        report = m.validate()  # shapes fetched from ONTOLOGY.source
    except Exception as exc:  # pragma: no cover - offline environments
        pytest.skip(f"could not fetch 223 shapes: {exc}")
    assert report.ok, str(report)
    assert report.violations == ()
    # dangling boundary CPs are advisory only (info severity)
    assert all(i.severity == "info" for i in report.issues)


def test_quickstart_example_runs(tmp_path):
    import runpy
    import shutil
    from pathlib import Path

    example = (
        Path(__file__).parent.parent
        / "examples"
        / "s223"
        / "ahu"
        / "s223_quickstart.py"
    )
    target = tmp_path / "s223_quickstart.py"
    shutil.copy(example, target)
    runpy.run_path(str(target))
    assert (tmp_path / "ahu.ttl").exists()


def test_system_scope_collects_members_and_resolved_boundaries(m):
    source = s223.Chiller("source")
    with m.system("transfer-system", label="Transfer system") as scope:
        pump_1 = s223.Pump("pump-1")
        pump_2 = s223.Pump("pump-2")
        pump_1 >> pump_2
    target = s223.Chiller("target")
    source >> pump_1
    pump_2 >> target

    resolved = m.resolve()
    system = resolved["transfer-system"]
    assert scope.entity is not None
    assert {member.name for member in system.has_member} == {"pump-1", "pump-2"}
    assert {point.owner.name for point in system.has_boundary_connection_point} == {
        "pump-1",
        "pump-2",
    }


def test_system_scope_boundary_after_the_block_reaches_the_system(m):
    source = s223.Chiller("source")
    with m.system("transfer-system") as scope:
        pump = s223.Pump("pump")
    source >> pump
    discharge = pump.port(
        "discharge", direction="out", medium=s223.enums.values.Fluid_Water
    )
    scope.boundary(discharge)

    resolved = m.resolve()
    boundary = resolved["transfer-system"].has_boundary_connection_point
    assert "discharge" in {point.name for point in boundary}


# -- maps_to on deferred ports ---------------------------------------------


def _ahu_with_coil(model):
    from plumb.s223.hvac import AirWaterCoolingCoil

    with s223.AirHandlingUnit("ahu") as ahu:
        coil = AirWaterCoolingCoil("coil")
    chiller = s223.Chiller("chiller")
    return ahu, coil, chiller


def test_port_maps_to_container_port_and_validates(m):
    ahu, coil, chiller = _ahu_with_coil(m)
    chw_in = ahu.port("chw-in", direction="in")
    chw_out = ahu.port("chw-out", direction="out")
    coil.water_inlet.maps_to = chw_in
    coil.water_outlet.maps_to = chw_out
    coil.air_inlet.maps_to = m["ahu-in"]
    coil.air_outlet.maps_to = m["ahu-out"]
    connect(chiller, chw_in, name="chw-supply")
    connect(chw_out, chiller, name="chw-return")
    assert coil.water_inlet.maps_to is chw_in

    resolved = m.resolve()
    inner = resolved["coil-water_inlet"]
    assert inner.maps_to is resolved["chw-in"]
    assert resolved["chw-in"].medium is enums.values.Fluid_Water
    assert resolved["coil-air_outlet"].maps_to is resolved["ahu-out"]
    assert resolved["chiller"].find_all_next(type(coil), descend=True) == [
        resolved["coil"]
    ]
    assert m.validate().ok


def test_concrete_point_maps_to_port(m):
    ahu, coil, chiller = _ahu_with_coil(m)
    with m:
        damper = s223.Damper("damper")
    ahu.contains(damper)
    inlet = ahu.port("mixed-air", direction="in")
    m["damper-in"].maps_to = inlet
    resolved = m.resolve()
    assert resolved["damper-in"].maps_to is resolved["mixed-air"]
    assert resolved["mixed-air"].medium is resolved["damper-in"].medium


def test_mapped_ports_share_a_medium(m):
    ahu, coil, chiller = _ahu_with_coil(m)
    coil.water_inlet.maps_to = ahu.port(
        "chw-in", direction="in", medium=enums.values.Fluid_Air
    )
    with pytest.raises(UnsatisfiableModelError, match="same medium"):
        m.resolve()


def test_mapped_ports_face_the_same_way(m):
    ahu, coil, chiller = _ahu_with_coil(m)
    coil.water_inlet.maps_to = ahu.port("chw-out", direction="out")
    with pytest.raises(UnsatisfiableModelError, match="same way"):
        m.resolve()


def test_maps_to_rejects_own_equipment_and_other_models(m):
    ahu, coil, chiller = _ahu_with_coil(m)
    with pytest.raises(ModelingError, match="its own equipment"):
        coil.water_inlet.maps_to = coil.water_outlet
    with pytest.raises(TypeError, match="port or connection point"):
        coil.water_inlet.maps_to = ahu
    with Model("urn:test/other#"):
        other = s223.AirHandlingUnit("other-ahu")
    with pytest.raises(ValueError, match="another Model"):
        coil.water_inlet.maps_to = other.port("chw-in", direction="in")


def test_changing_maps_to_invalidates_resolution(m):
    ahu, coil, chiller = _ahu_with_coil(m)
    first = ahu.port("chw-a", direction="in")
    second = ahu.port("chw-b", direction="in")
    coil.water_inlet.maps_to = first
    assert m.resolve()["coil-water_inlet"].maps_to.name == "chw-a"
    coil.water_inlet.maps_to = second
    assert m.resolve()["coil-water_inlet"].maps_to.name == "chw-b"
    coil.water_inlet.maps_to = None
    assert m.resolve()["coil-water_inlet"].maps_to is None


@pytest.mark.parametrize(
    ("point_class", "as_source"),
    [
        (s223.OutletConnectionPoint, True),
        (s223.InletConnectionPoint, False),
        (s223.BidirectionalConnectionPoint, True),
        (s223.BidirectionalConnectionPoint, False),
    ],
)
def test_point_eligibility_uses_rdf_ancestry_after_mro_repair(point_class, as_source):
    from plumb.core import ClassInfo, OntologyInfo, Registry

    registry = Registry(OntologyInfo("Projected points", "urn:projected-points"))
    registry.include(s223.REGISTRY)

    # Model a direction ancestor omitted from the emitted Python bases.
    class ProjectedPoint(s223.ConnectionPoint):
        _classinfo = ClassInfo(
            "urn:projected-points#Point",
            registry.ontology,
            registry,
            parent_iris=(point_class.meta.iri,),
            ancestor_iris=(point_class.meta.iri, s223.ConnectionPoint.meta.iri),
        )

    with Model("urn:test/projected-direction#") as model:
        source, target = s223.Equipment("source"), s223.Equipment("target")
        projected = ProjectedPoint(
            "projected",
            medium=enums.values.Fluid_Air,
            owner=source if as_source else target,
        )
        other_class = (
            s223.InletConnectionPoint if as_source else s223.OutletConnectionPoint
        )
        other = other_class(
            "other",
            medium=enums.values.Fluid_Air,
            owner=target if as_source else source,
        )
        handle = connect(projected, other) if as_source else connect(other, projected)
    assert model.check().complete
    snapshot = model.resolve()
    assert snapshot["projected"] in snapshot.connection(handle).connects_at


def test_point_eligibility_ignores_misleading_python_class_names():
    from plumb.core import ClassInfo, OntologyInfo, Registry

    registry = Registry(OntologyInfo("Renamed points", "urn:renamed-points"))
    registry.include(s223.REGISTRY)

    class OutletConnectionPoint(s223.InletConnectionPoint):
        _classinfo = ClassInfo(
            "urn:renamed-points#Inlet",
            registry.ontology,
            registry,
            parent_iris=(s223.InletConnectionPoint.meta.iri,),
            ancestor_iris=(
                s223.InletConnectionPoint.meta.iri,
                s223.ConnectionPoint.meta.iri,
            ),
        )

    with Model("urn:test/renamed-direction#") as model:
        source, target = s223.Equipment("source"), s223.Equipment("target")
        wrong = OutletConnectionPoint(
            "wrong", owner=source, medium=enums.values.Fluid_Air
        )
        inlet = s223.InletConnectionPoint(
            "inlet", owner=target, medium=enums.values.Fluid_Air
        )
        connect(wrong, inlet)
    assert model.check().status == "unsatisfiable"
