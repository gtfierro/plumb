"""QUDT-backed quantities and compiled unit/quantity-kind vocabularies."""

from __future__ import annotations

from typing import Any, Literal, TypeVar, cast

from plumb.core import (
    ClassInfo,
    ConnectionHandle,
    Entity,
    EnumValue,
    Lit,
    Model,
    PortHandle,
    OntologyInfo,
    PropertySpec,
    Registry,
    TermOne,
    TermValue,
)

from . import quantity_kinds, units
from plumb.core.property_schema import QuantityAmount

QUDT = "http://qudt.org/schema/qudt/"
ONTOLOGY = OntologyInfo(
    name="QUDT",
    iri="http://qudt.org/3.4.0/qudt-all",
    version="3.4.0",
    source="http://qudt.org/3.4.0/qudt-all",
)
_REGISTRY = Registry(ONTOLOGY)
REGISTRY = _REGISTRY
PropertyT = TypeVar("PropertyT", bound=Entity)
PropertyCapability = Literal["static", "observable", "actuatable"]


def _quantity_class(registry: Registry, capability: PropertyCapability) -> type[Entity]:
    class_names = {
        "static": "QuantifiableProperty",
        "observable": "QuantifiableObservableProperty",
        "actuatable": "QuantifiableActuatableProperty",
    }
    try:
        class_name = class_names[capability]
    except KeyError:
        raise ValueError(f"unknown property capability {capability!r}") from None
    property_class = registry.by_iri.get(
        f"http://data.ashrae.org/standard223#{class_name}"
    )
    if property_class is None:
        raise TypeError(f"{registry.ontology.name} has no {class_name} class")
    return property_class


_NUMERIC_VALUE = PropertySpec(
    name="numeric_value",
    predicate=f"{QUDT}numericValue",
    kind="literal",
    datatype=float,
    required=True,
    max_count=1,
)
_HAS_UNIT = PropertySpec(
    name="has_unit",
    predicate=f"{QUDT}hasUnit",
    kind="term",
    required=True,
    max_count=1,
    term_ranges=(f"{QUDT}Unit",),
)


class QuantityValue(Entity):
    """A QUDT numeric value paired with its unit."""

    _classinfo = ClassInfo(
        iri=f"{QUDT}QuantityValue",
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        properties=(_NUMERIC_VALUE, _HAS_UNIT),
    )

    numeric_value: Lit[float] = Lit(_NUMERIC_VALUE)
    has_unit: TermOne[TermValue] = TermOne(_HAS_UNIT)

    def __init__(
        self,
        name: str | None = None,
        *,
        numeric_value: float,
        has_unit: TermValue,
        label: str | None = None,
        comment: str | None = None,
        model: Model | None = None,
    ) -> None:
        super().__init__(
            name,
            label=label,
            comment=comment,
            model=model,
            numeric_value=numeric_value,
            has_unit=has_unit,
        )


def _create_quantity(
    property_class: type[PropertyT],
    name: str,
    value: float | None,
    unit: TermValue,
    quantity_kind: TermValue,
    *,
    of: Entity | ConnectionHandle | PortHandle | None = None,
    datatype: str | None = None,
    **properties: Any,
) -> PropertyT:
    """Instantiate an S223 property with a scalar value and QUDT context.

    ``value`` may be None for an observed or actuated property whose value
    lives outside the model.

    ``property_class`` remains explicit because the ontology, not this helper,
    determines whether the property is observable, actuatable, or static.
    """
    if not unit.is_instance_of(f"{QUDT}Unit"):
        raise TypeError(f"unit must be a QUDT Unit term, got {unit!r}")
    if not quantity_kind.is_instance_of(f"{QUDT}QuantityKind"):
        raise TypeError(
            f"quantity_kind must be a QUDT QuantityKind term, got {quantity_kind!r}"
        )
    model = (
        (of.meta.model if isinstance(of, Entity) else of._model)
        if of is not None
        else properties.get("model")
    )
    properties.setdefault("model", model)
    constructor: Any = property_class
    prop = constructor(
        name,
        has_quantity_kind=quantity_kind,
        has_unit=unit,
        has_value=value,
        **properties,
    )
    if datatype is not None and value is not None:
        from rdflib import Literal, URIRef

        prop._data["has_value"] = Literal(value, datatype=URIRef(datatype))
        prop.meta.model._touch(prop)
    if of is not None:
        _attach_property(prop, of)
    return cast(PropertyT, prop)


def _attach_property(prop: Entity, of: Entity | ConnectionHandle | PortHandle) -> None:
    if isinstance(of, PortHandle):
        of._properties.append(prop)
        of._model._touch(of.owner)
    else:
        getattr(of, "has_property").add(prop)


def _attached_quantity(
    target: Entity | PortHandle | ConnectionHandle,
    name: str,
    value: float | QuantityAmount,
    *,
    unit: TermValue | None,
    kind: TermValue,
    capability: Literal["static", "observable", "actuatable"] = "static",
    label: str | None = None,
    **properties: Any,
) -> Entity:
    """Shared scalar construction for concrete and deferred subjects."""
    from plumb.core.property_schema import QuantityDefinition

    if isinstance(value, QuantityAmount):
        if unit is not None and unit.iri != value.unit.iri:
            raise ValueError("explicit amount and unit argument disagree")
        unit = value.unit
    if unit is None:
        raise TypeError("supply unit= or a QuantityAmount")
    definition = QuantityDefinition(name, "scalar quantity", kind, unit)
    number, selected_unit = definition.unpack(value)
    registry, model = _context(target)
    with model._atomic():
        return _create_quantity(
            _quantity_class(registry, capability),
            name,
            number,
            selected_unit,
            kind,
            of=target,
            label=label,
            **properties,
        )


_S223 = "http://data.ashrae.org/standard223#"
_LOCATIONS = tuple(
    f"{_S223}{name}" for name in ("Connectable", "Connection", "ConnectionPoint")
)


def _context(target: Entity | PortHandle | ConnectionHandle) -> tuple[Registry, Model]:
    # A deferred location has no concrete RDF subject yet, but its property
    # still belongs to the same model. Select schema policy from the endpoint
    # owners AND referenced medium: a WaTr enum on canonical S223 equipment
    # can be the only evidence that the water vocabulary/profile is in use.
    from plumb.core import Registry
    from plumb.core.points import endpoint_owner

    if isinstance(target, Entity):
        owner = endpoint_owner(target)
        return Registry.for_entities([target, owner]), target.meta.model
    if isinstance(target, PortHandle):
        return Registry.for_entities(
            [target.owner], values=[target.medium]
        ), target._model
    return Registry.for_entities(
        [endpoint_owner(target.source), endpoint_owner(target.target)],
        values=[target.medium],
    ), target._model


def _s223_class(registry: Registry, name: str) -> Any:
    cls = registry.by_iri.get(f"{_S223}{name}")
    if cls is None:
        raise TypeError(f"{registry.ontology.name} has no {name} class")
    return cls


def _dynamic_property(
    target: Entity | PortHandle | ConnectionHandle,
    name: str,
    *,
    kind: TermValue | EnumValue,
    unit: TermValue | None,
    value: float | QuantityAmount | EnumValue | None,
    capability: Literal["observable", "actuatable"],
    properties: dict[str, Any],
) -> Entity:
    """An observable or actuatable property, quantified or enumerated.

    A QUDT quantity kind needs a unit; an enumeration kind such as
    ``Binary_OnOff`` takes none, and its value must be one of the kind's
    members.
    """
    from plumb.core.property_schema import QuantityDefinition

    registry, model = _context(target)
    if isinstance(kind, EnumValue):
        if unit is not None:
            raise TypeError(f"{name}: an enumeration kind takes no unit")
        if value is not None and not (
            isinstance(value, EnumValue) and value is not kind and value.is_a(kind)
        ):
            raise ValueError(f"{name}: value must be a member of {kind!r}")
        prefix = "Observable" if capability == "observable" else "Actuatable"
        prop = _s223_class(registry, f"Enumerated{prefix}Property")(
            name, has_enumeration_kind=kind, has_value=value, model=model, **properties
        )
        _attach_property(prop, target)
        return prop
    if isinstance(value, EnumValue):
        raise TypeError(f"{name}: a quantity takes a number, not {value!r}")
    if isinstance(value, QuantityAmount):
        if unit is not None and unit.iri != value.unit.iri:
            raise ValueError("explicit amount and unit argument disagree")
        unit = value.unit
    if unit is None:
        raise TypeError("supply unit= or a QuantityAmount value")
    # Constructing the definition checks that the unit fits the kind.
    definition = QuantityDefinition(name, "dynamic property", kind, unit)
    number: float | None = None
    if value is not None:
        number, unit = definition.unpack(value)
    return _create_quantity(
        _quantity_class(registry, capability),
        name,
        number,
        unit,
        kind,
        of=target,
        **properties,
    )


def _attached_sensor(
    target: Entity | PortHandle | ConnectionHandle,
    name: str,
    *,
    kind: TermValue | EnumValue,
    unit: TermValue | None = None,
    sensor_class: type[Entity] | None = None,
    value: float | QuantityAmount | EnumValue | None = None,
    label: str | None = None,
    **properties: Any,
) -> Entity:
    """Create an observed property on ``target`` and a sensor observing it.

    The sensor is named ``name`` and observes ``<name>-value``. Without
    ``sensor_class``, the package's quantity-kind table picks the most
    specific sensor class, falling back to ``Sensor``.
    """
    registry, model = _context(target)
    if isinstance(target, Entity) and not any(
        target.meta.is_a(iri) for iri in _LOCATIONS
    ):
        raise TypeError(
            f"{target.type} cannot be a sensor's observation location; use "
            "equipment, a connection, or a connection point"
        )
    base = _s223_class(registry, "Sensor")
    if sensor_class is None:
        chosen = registry.sensor_classes.get(kind.iri)
        sensor_class = registry.resolve(chosen) if chosen is not None else base
    elif not (
        isinstance(sensor_class, type) and issubclass(sensor_class, base.meta.canonical)
    ):
        raise TypeError(f"sensor_class must be a Sensor subclass, got {sensor_class!r}")
    constructor: Any = sensor_class
    with model._atomic():
        observed = _dynamic_property(
            target,
            f"{name}-value",
            kind=kind,
            unit=unit,
            value=value,
            capability="observable",
            properties=properties,
        )
        return constructor(
            name,
            has_observation_location=target,
            observes=observed,
            label=label,
            model=model,
        )


def _attached_actuator(
    target: Entity,
    name: str,
    *,
    kind: TermValue | EnumValue,
    unit: TermValue | None = None,
    value: float | QuantityAmount | EnumValue | None = None,
    label: str | None = None,
    **properties: Any,
) -> Entity:
    """Create a command property on equipment and an actuator driven by it.

    The actuator is named ``name``; the equipment and the actuator are both
    ``actuated_by_property`` the ``<name>-command`` property, and the
    actuator ``actuates`` the equipment.
    """
    registry, model = _context(target)
    if not target.meta.is_a(_s223_class(registry, "Equipment")):
        raise TypeError(f"{target.type} is not Equipment, so it cannot be actuated")
    with model._atomic():
        command = _dynamic_property(
            target,
            f"{name}-command",
            kind=kind,
            unit=unit,
            value=value,
            capability="actuatable",
            properties=properties,
        )
        getattr(target, "actuated_by_property").add(command)
        return _s223_class(registry, "Actuator")(
            name,
            actuates=[target],
            actuated_by_property=[command],
            label=label,
            model=model,
        )


__all__ = [
    "ONTOLOGY",
    "REGISTRY",
    "QuantityValue",
    "QuantityAmount",
    "quantity_kinds",
    "units",
]
