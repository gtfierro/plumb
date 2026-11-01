"""The .meta accessor, required-property enforcement, abstract classes."""

import pytest
import toy

from plumb import Model, ModelingError


@pytest.fixture
def m():
    with Model("urn:ex/t#") as model:
        yield model


def test_class_meta_fields():
    meta = toy.Fan.meta
    assert meta.iri == "urn:toy#Fan"
    assert meta.label == "Fan"
    assert meta.definition == "A device that moves air."
    assert meta.ontology.name == "Toy"
    assert meta.ontology.iri == "urn:toy"
    assert meta.parents == (toy.Equipment,)


def test_effective_properties_include_inherited():
    names = {spec.name for spec in toy.Fan.meta.properties}
    assert {"feeds", "fed_by", "has_part", "has_location", "rated_power"} <= names


def test_subclass_narrowing_shadows_parent_spec():
    spec = {s.name: s for s in toy.Meter.meta.properties}["has_point"]
    assert spec.required  # Meter narrowed it; Equipment's version is not
    parent = {s.name: s for s in toy.Equipment.meta.properties}["has_point"]
    assert not parent.required


def test_instance_meta(m):
    fan = toy.Fan("f1")
    assert fan.meta.cls is toy.Fan
    assert fan.meta.instance_iri == "urn:ex/t#f1"
    assert fan.meta.model is m
    assert fan.meta.iri == "urn:toy#Fan"  # class provenance still reachable


def test_required_property_enforced_at_construction(m):
    with pytest.raises(ModelingError, match="missing required property: has_point"):
        toy.Meter("m1")
    sensor = toy.Sensor("s1")
    meter = toy.Meter("m1", has_point=[sensor])
    assert sensor in meter.has_point


def test_abstract_class_rejected(m):
    with pytest.raises(ModelingError, match="organizational class"):
        toy.Organizational("x")


def test_entity_base_cannot_be_instantiated(m):
    from plumb import Entity

    with pytest.raises(TypeError, match="cannot be instantiated directly"):
        Entity("x")


def test_registry_lookup():
    reg = toy.Fan.meta.registry
    assert reg.resolve("Equipment") is toy.Equipment
    assert reg.by_iri["urn:toy#Sensor"] is toy.Sensor
    with pytest.raises(KeyError, match="not registered"):
        reg.resolve("Nope")


def test_label_and_comment_are_mutable(m):
    fan = toy.Fan("f1")
    assert fan.label == "f1"
    fan.label = "Supply Fan"
    fan.comment = "rooftop unit"
    assert fan.label == "Supply Fan"
    assert fan.comment == "rooftop unit"


@pytest.mark.parametrize("reverse", [False, True])
def test_registry_selects_explicit_nominal_view_in_both_orders(reverse):
    from plumb.core import ClassInfo, Entity, OntologyInfo, Registry

    base = Registry(OntologyInfo("Base", "urn:view-base"))
    extension = Registry(OntologyInfo("Extension", "urn:view-extension"))

    class Original(Entity):
        _classinfo = ClassInfo("urn:view#Term", base.ontology, base)

    extension.include(base)

    class Extended(Original):
        _classinfo = ClassInfo(
            Original.meta.iri, extension.ontology, extension, canonical=Original
        )

    assert Extended.meta.canonical is Original
    assert base.by_iri[Original.meta.iri] is Original
    registries = [base, extension]
    if reverse:
        registries.reverse()
    selected = Registry(OntologyInfo("Selected", "urn:selected"))
    for registry in registries:
        selected.include(registry)
    assert selected.by_iri[Original.meta.iri] is Extended


def test_registry_rejects_incompatible_views_without_partial_changes():
    from plumb.core import ClassInfo, Entity, OntologyInfo, Registry

    base = Registry(OntologyInfo("Base", "urn:view-base"))
    left = Registry(OntologyInfo("Left", "urn:view-left"))
    right = Registry(OntologyInfo("Right", "urn:view-right"))

    class Original(Entity):
        _classinfo = ClassInfo("urn:view#Term", base.ontology, base)

    class Left(Original):
        _classinfo = ClassInfo(
            Original.meta.iri, left.ontology, left, canonical=Original
        )

    class Right(Original):
        _classinfo = ClassInfo(
            Original.meta.iri, right.ontology, right, canonical=Original
        )

    before = dict(left.by_iri)
    with pytest.raises(ValueError, match="incompatible imported views"):
        left.include(right)
    assert left.by_iri == before


def test_view_requires_the_canonical_python_base():
    from plumb.core import ClassInfo, Entity, OntologyInfo, Registry

    base = Registry(OntologyInfo("Base", "urn:view-base"))
    extension = Registry(OntologyInfo("Extension", "urn:view-extension"))

    class Original(Entity):
        _classinfo = ClassInfo("urn:view#Term", base.ontology, base)

    with pytest.raises(ValueError, match="invalid canonical class"):

        class Invalid(Entity):
            _classinfo = ClassInfo(
                Original.meta.iri, extension.ontology, extension, canonical=Original
            )
