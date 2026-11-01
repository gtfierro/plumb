"""Typed property values and measurement metadata compiled from SHACL."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
import dataclasses
from dataclasses import MISSING, dataclass, fields
from math import isfinite
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar, dataclass_transform

from . import containment
from .terms import TermValue

if TYPE_CHECKING:
    from .entity import Entity
    from .enums import EnumValue
    from .points import PointRef
    from .resolution import ConnectionHandle, PortHandle


@dataclass(frozen=True)
class QuantityAmount:
    """A model-independent numeric value with an explicit QUDT unit."""

    value: float
    unit: TermValue

    def __post_init__(self) -> None:
        _number(self.value)
        if not isinstance(self.unit, TermValue) or not self.unit.is_instance_of(
            "http://qudt.org/schema/qudt/Unit"
        ):
            raise TypeError("unit must be a compiled QUDT Unit")


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("quantity value must be a number")
    if not isfinite(value):
        raise ValueError("quantity value must be finite")
    return float(value)


@dataclass(frozen=True)
class QuantityDefinition:
    """Immutable measurement semantics projected from a source property shape."""

    name: str
    source_shape: str
    kind: TermValue
    unit: TermValue
    datatype: str = "http://www.w3.org/2001/XMLSchema#double"
    label: str | None = None
    description: str | None = None
    notation: str | None = None
    local_name: str | None = None
    fixed_unit: bool = False
    allowed_units: tuple[TermValue, ...] = ()
    of_medium: EnumValue | None = None
    of_substance: EnumValue | None = None
    aspects: tuple[EnumValue, ...] = ()
    property_class: type[Entity] | None = None
    properties: tuple[tuple[str, Any], ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    allowed_values: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        if not self.kind.is_instance_of("http://qudt.org/schema/qudt/QuantityKind"):
            raise TypeError(f"{self.name}: kind must be a QUDT QuantityKind")
        self.unpack(QuantityAmount(0.0, self.unit), check_value=False)

    def unpack(
        self, value: float | QuantityAmount, *, check_value: bool = True
    ) -> tuple[float, TermValue]:
        amount = (
            value
            if isinstance(value, QuantityAmount)
            else QuantityAmount(value, self.unit)
        )
        unit = amount.unit
        if unit.iri != self.unit.iri:
            if self.fixed_unit:
                raise ValueError(
                    f"{self.name}: source shape fixes unit to {self.unit.iri}"
                )
            expected = self.kind.dimension_vector or self.unit.dimension_vector
            if expected is None or unit.dimension_vector is None:
                raise ValueError(
                    f"{self.name}: unit compatibility is unknown for {unit.iri}"
                )
            if unit.dimension_vector != expected:
                raise ValueError(f"{self.name}: incompatible unit {unit.iri}")
        elif (
            self.kind.dimension_vector is not None
            and unit.dimension_vector is not None
            and self.kind.dimension_vector != unit.dimension_vector
        ):
            raise ValueError(f"{self.name}: unit and quantity kind are incompatible")
        if self.allowed_units and unit.iri not in {
            item.iri for item in self.allowed_units
        }:
            raise ValueError(f"{self.name}: unit is not permitted by the source shape")
        number = _number(amount.value)
        if check_value:
            if self.minimum is not None and number < self.minimum:
                raise ValueError(f"{self.name}: value must be >= {self.minimum}")
            if self.maximum is not None and number > self.maximum:
                raise ValueError(f"{self.name}: value must be <= {self.maximum}")
            if self.allowed_values and number not in self.allowed_values:
                raise ValueError(
                    f"{self.name}: value must be one of {self.allowed_values}"
                )
        return number, unit


_QUANTITY = "plumb.quantity"


def quantity_field(
    *,
    kind: TermValue,
    unit: TermValue,
    default: float | QuantityAmount | Any = MISSING,
    label: str | None = None,
    description: str | None = None,
    local_name: str | None = None,
    of_medium: EnumValue | None = None,
    of_substance: EnumValue | None = None,
    aspects: tuple[EnumValue, ...] = (),
    property_class: type[Entity] | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
    allowed_units: tuple[TermValue, ...] = (),
    fixed_unit: bool = False,
) -> Any:
    """Declare one quantity of a :class:`PropertySchema` written in Python.

    ``kind`` and ``unit`` are QUDT terms; ``unit`` is the default for bare
    numbers. The other arguments mirror what a SHACL property shape supplies
    to a generated schema. Omit ``default`` to make the value required.
    """
    spec = {
        "kind": kind,
        "unit": unit,
        "label": label,
        "description": description,
        "local_name": local_name,
        "of_medium": of_medium,
        "of_substance": of_substance,
        "aspects": tuple(aspects),
        "property_class": property_class,
        "minimum": minimum,
        "maximum": maximum,
        "allowed_units": tuple(allowed_units),
        "fixed_unit": fixed_unit,
    }
    return dataclasses.field(default=default, metadata={_QUANTITY: spec})


@dataclass_transform(
    kw_only_default=True, frozen_default=True, field_specifiers=(quantity_field,)
)
@dataclass(frozen=True, kw_only=True)
class PropertySchema:
    """Base for frozen value schemas with explicit typed constructors.

    Schemas are usually generated from SHACL. A subclass written in Python
    declares each field with :func:`quantity_field` and becomes a frozen,
    keyword-only dataclass without a decorator.
    """

    _definitions: ClassVar[tuple[QuantityDefinition, ...]] = ()
    source_shape: ClassVar[str] = ""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Generated schemas list their definitions and apply @dataclass
        # themselves; doing it here too would fail on the frozen class.
        if "_definitions" in cls.__dict__:
            return
        dataclass(frozen=True, kw_only=True)(cls)
        origin = f"{cls.__module__}.{cls.__qualname__}"
        missing = [item.name for item in fields(cls) if _QUANTITY not in item.metadata]
        if missing:
            raise TypeError(
                f"{cls.__name__}: declare {', '.join(missing)} with quantity_field()"
            )
        cls.source_shape = origin
        cls._definitions = tuple(
            QuantityDefinition(
                name=item.name,
                source_shape=f"{origin}.{item.name}",
                **item.metadata[_QUANTITY],
            )
            for item in fields(cls)
        )

    def __post_init__(self) -> None:
        for definition in self._definitions:
            definition.unpack(getattr(self, definition.name))

    @classmethod
    def describe(cls) -> str:
        """Describe fields, model notation, units, and source shape provenance."""
        lines = [cls.__doc__ or cls.__name__]
        defaults = {field.name: field.default for field in fields(cls)}
        for field in cls._definitions:
            notation = f" ({field.notation})" if field.notation else ""
            default = defaults[field.name]
            value = "required" if default is MISSING else f"default={default!r}"
            lines.append(
                f"{field.name}{notation}: {field.kind.label or field.kind.iri} "
                f"[{field.unit.label or field.unit.iri}; {field.unit.iri}] "
                f"{value} — {field.source_shape}"
            )
            qualifications = []
            if field.of_substance is not None:
                qualifications.append(
                    f"substance={field.of_substance.label or field.of_substance.iri}"
                )
            if field.of_medium is not None:
                qualifications.append(
                    f"medium={field.of_medium.label or field.of_medium.iri}"
                )
            if field.aspects:
                qualifications.append(
                    "aspects="
                    + ", ".join(item.label or item.iri for item in field.aspects)
                )
            if field.property_class is not None:
                qualifications.append(f"property_class={field.property_class.__name__}")
            if qualifications:
                lines.append("  " + "; ".join(qualifications))
            if field.description:
                lines.append("  " + field.description)
        return "\n".join(lines)


class PropertySet(Mapping[str, "Entity"]):
    """Read-only mapping from schema field names to newly attached entities."""

    def __init__(self, properties: Mapping[str, Entity]) -> None:
        self._properties = MappingProxyType(dict(properties))

    def __getitem__(self, key: str) -> Entity:
        return self._properties[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._properties)

    def __len__(self) -> int:
        return len(self._properties)


def apply_properties(
    target: Entity | PortHandle | PointRef | ConnectionHandle,
    schema: PropertySchema,
    *,
    prefix: str | None = None,
) -> PropertySet:
    """Atomically attach a generated schema to its exact authored subject."""
    from .entity import Entity
    from .points import PointRef
    from .resolution import ConnectionHandle, PortHandle
    from plumb.qudt import _quantity_class, _create_quantity, _context

    if not isinstance(schema, PropertySchema):
        raise TypeError("properties must be an instance of a generated PropertySchema")
    if isinstance(target, PointRef):
        target = target._port
    if isinstance(target, Entity):
        if not hasattr(target, "has_property"):
            raise TypeError(f"{target.type} has no has_property relation")
        model = target.meta.model
    elif isinstance(target, PortHandle):
        model = target._model
    elif isinstance(target, ConnectionHandle):
        model = target._model
    else:
        raise TypeError("target must support RDF properties")
    registry, model = _context(target)
    model._assert_mutable()
    stem = target.name if prefix is None else prefix
    if not stem:
        raise ValueError("property prefix must not be empty")
    prepared = []
    for definition in schema._definitions:
        value, unit = definition.unpack(getattr(schema, definition.name))
        name = f"{stem}-{definition.local_name or definition.name.replace('_', '-')}"
        prepared.append((definition, name, value, unit))
    names = [item[1] for item in prepared]
    if len(set(names)) != len(names) or any(
        name in model._by_name or name in model._reserved_names for name in names
    ):
        raise ValueError("property schema would create duplicate model names")
    created: dict[str, Entity] = {}
    with model._atomic(), containment.suppressed():
        for definition, name, value, unit in prepared:
            properties = dict(definition.properties)
            if definition.of_medium is not None:
                properties["of_medium"] = definition.of_medium
            if definition.of_substance is not None:
                properties["of_substance"] = definition.of_substance
            if definition.aspects:
                properties["has_aspect"] = definition.aspects
            cls = (
                registry.by_iri.get(
                    definition.property_class.meta.iri, definition.property_class
                )
                if definition.property_class is not None
                else _quantity_class(registry, "static")
            )
            prop = _create_quantity(
                cls,
                name,
                value,
                unit,
                definition.kind,
                datatype=definition.datatype,
                of=target,
                label=definition.label,
                **properties,
            )
            created[definition.name] = prop
    return PropertySet(created)
