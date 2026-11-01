"""Prototype: canonical S223 classes and model-scoped extension shapes."""

import importlib
import os
from pathlib import Path
import subprocess
import sys

import pytest
from rdflib import Graph, URIRef

from plumb import Model, connect, s223
from plumb.core.errors import RangeError
from plumb.gen import generate
from plumb.gen.overlays import Overlay
from plumb.qudt import quantity_kinds, units

PREFIXES = """
@prefix s223: <http://data.ashrae.org/standard223#> .
@prefix water: <urn:profile:water#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix codegen: <https://watermetadata.org/plumb/codegen#> .
"""
PROFILE = """
<urn:profile:water> a owl:Ontology ; codegen:baseModule "plumb.s223" .
water:WaterTemperature a owl:Class ;
    rdfs:subClassOf s223:QuantifiableObservableProperty .
water:WaterEquipment a owl:Class ; rdfs:subClassOf s223:Equipment .
water:TemperatureLimit a sh:NodeShape ;
    sh:targetClass s223:QuantifiableObservableProperty ;
    sh:property water:ValueLimit .
water:ValueLimit sh:path s223:hasValue ; sh:maxInclusive 100.0 .
"""


@pytest.fixture
def profile(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(tmp_path))
    generate(
        Graph().parse(data=PREFIXES + PROFILE, format="turtle"),
        tmp_path / "prototype_water",
        name="WaterProfile",
    )
    yield importlib.import_module("prototype_water")
    for name in list(sys.modules):
        if name.startswith("prototype_"):
            sys.modules.pop(name, None)


def temperature(cls, name, value):
    return cls(
        name,
        has_value=value,
        has_quantity_kind=quantity_kinds.Temperature,
        has_unit=units.DEG_C,
    )


def test_imported_classes_and_enums_keep_canonical_identity(profile):
    registry = profile.REGISTRY
    assert registry.by_iri[s223.Equipment.meta.iri] is s223.Equipment
    assert registry.by_iri[s223.Property.meta.iri] is s223.Property
    assert (
        registry.resolve_enum(s223.enums.values.Fluid_Water.iri)
        is s223.enums.values.Fluid_Water
    )
    assert issubclass(profile.WaterTemperature, s223.QuantifiableObservableProperty)
    with Model("urn:profile:identity#"):
        fan = s223.Fan("fan")
        property_ = temperature(profile.WaterTemperature, "temperature", 20.0)
        fan.has_property.add(property_)
        assert property_ in fan.has_property
        with pytest.raises(RangeError):
            fan.has_property.add(profile.WaterEquipment("equipment"))


def test_profile_restrictions_are_model_scoped_and_do_not_mutate_shared_classes(
    profile,
):
    with Model("urn:profile:base#") as plain:
        temperature(s223.QuantifiableObservableProperty, "temperature", 120.0)
    assert plain.validate(infer=False)
    with Model("urn:profile:mixed#") as mixed:
        temperature(s223.QuantifiableObservableProperty, "shared", 120.0)
        temperature(profile.WaterTemperature, "local", 20.0)
    report = mixed.validate(infer=False)
    assert not report
    assert {issue.entity.name for issue in report.violations if issue.entity} == {
        "shared"
    }
    # A profile-only numeric bound is a graph constraint. The canonical
    # constructor and its defining registry remain unchanged in both models.
    assert s223.QuantifiableObservableProperty.meta.registry is s223.REGISTRY
    assert plain.validate(infer=False)


@pytest.mark.parametrize("reverse", [False, True])
def test_hydration_retains_profile_when_only_canonical_classes_are_present(
    profile, reverse
):
    with Model("urn:profile:loaded#") as source:
        temperature(s223.QuantifiableObservableProperty, "temperature", 120.0)
    registries = [s223.REGISTRY, profile.REGISTRY]
    if reverse:
        registries.reverse()
    loaded = Model.from_graph(source.graph(), registries=registries)
    assert type(loaded["temperature"]) is s223.QuantifiableObservableProperty
    assert not loaded.validate(infer=False)
    assert (
        URIRef("urn:profile:water#ValueLimit"),
        None,
        None,
    ) in loaded.export_ontology()
    snapshot = loaded.resolve()
    assert not snapshot._model.validate(infer=False)
    loaded["temperature"].has_value = 20.0
    assert loaded.validate(infer=False)
    assert source.validate(infer=False)


def test_transitive_profile_dependency_survives_hydration(profile, tmp_path):
    graph = Graph().parse(
        data=PREFIXES
        + """
        <urn:profile:plant> a owl:Ontology ;
            codegen:baseModule "prototype_water" .
        water:PlantTemperature a owl:Class ; rdfs:subClassOf water:WaterTemperature .
        """,
        format="turtle",
    )
    generate(graph, tmp_path / "prototype_plant", name="PlantProfile")
    plant = importlib.import_module("prototype_plant")
    with Model("urn:profile:transitive#") as source:
        temperature(s223.QuantifiableObservableProperty, "temperature", 120.0)
    loaded = Model.from_graph(source.graph(), registries=plant.REGISTRY)
    assert not loaded.validate(infer=False)


def test_mixed_containment_and_connections_use_the_canonical_backend(profile):
    with Model("urn:profile:connections#") as model:
        with s223.PhysicalSpace("room"):
            equipment = profile.WaterEquipment("equipment")
        source = s223.Chiller("source")
        handle = connect(source, equipment, medium=s223.enums.values.Fluid_Water)
    assert list(equipment.has_physical_location) == [model["room"]]
    pipe = model.resolve().connection(handle)
    assert type(pipe) is s223.Pipe
    assert pipe.medium is s223.enums.values.Fluid_Water


@pytest.mark.parametrize("reverse", [False, True])
def test_profile_import_order_cannot_change_s223_classes(profile, tmp_path, reverse):
    modules = ["plumb.s223", "prototype_water"]
    if reverse:
        modules.reverse()
    script = f"""
import importlib
for module in {modules!r}:
    importlib.import_module(module)
from plumb import s223
import prototype_water as water
assert water.REGISTRY.by_iri[s223.Equipment.meta.iri] is s223.Equipment
assert water.REGISTRY.resolve_enum(s223.enums.values.Fluid_Water.iri) is s223.enums.values.Fluid_Water
assert issubclass(water.WaterTemperature, s223.QuantifiableObservableProperty)
assert s223.QuantifiableObservableProperty.meta.registry is s223.REGISTRY
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_base_class_valued_links_hydrate_extension_terms(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(tmp_path))
    base = Graph().parse(
        data=PREFIXES
        + """
        <urn:profile:catalogue> a owl:Ontology .
        water:Category a owl:Class .
        water:Catalogue a owl:Class ; sh:property [
            sh:path water:accepts ; sh:class water:Category
        ] .
        """,
        format="turtle",
    )
    generate(
        base,
        tmp_path / "prototype_catalogue",
        name="Catalogue",
        overlay=Overlay(class_properties=("urn:profile:water#accepts",)),
    )
    generate(
        Graph().parse(
            data=PREFIXES
            + """
            <urn:profile:special> a owl:Ontology ;
                codegen:baseModule "prototype_catalogue" .
            water:WaterCategory a owl:Class ; rdfs:subClassOf water:Category .
            """,
            format="turtle",
        ),
        tmp_path / "prototype_special",
        name="SpecialCatalogue",
    )
    catalogue = importlib.import_module("prototype_catalogue")
    special = importlib.import_module("prototype_special")
    try:
        with Model("urn:profile:class-values#") as model:
            item = catalogue.Catalogue("catalogue", accepts=[special.WaterCategory])
        loaded = Model.from_graph(model.graph(), registries=special.REGISTRY)
        assert list(getattr(loaded[item.name], "accepts")) == [special.WaterCategory]
        assert catalogue.REGISTRY.by_iri.get(special.WaterCategory.meta.iri) is None
    finally:
        sys.modules.pop("prototype_catalogue", None)
        sys.modules.pop("prototype_special", None)


def test_linked_types_accept_subclasses_and_reject_unrelated_values(profile, tmp_path):
    positive = tmp_path / "positive.py"
    positive.write_text("""
from plumb.s223 import Fan, Property
from prototype_water import WaterTemperature

def link(fan: Fan, value: WaterTemperature) -> Property:
    fan.has_property.add(value)
    return value
""")
    negative = tmp_path / "negative.py"
    negative.write_text("""
from plumb.s223 import Fan
from prototype_water import WaterEquipment

def invalid(fan: Fan, value: WaterEquipment) -> None:
    fan.has_property.add(value)
""")
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
