"""Named point descriptors and references emitted by the SHACL compiler."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar, cast, overload

if TYPE_CHECKING:
    from .entity import Entity
    from .enums import EnumValue
    from .property_schema import PropertySchema, PropertySet, QuantityAmount
    from .terms import TermValue

P = TypeVar("P")


@dataclass(frozen=True)
class PointDeclaration(Generic[P]):
    """Internal descriptor for fixed point facts compiled from SHACL."""

    count: int = 1
    medium: EnumValue | None = None
    direction: str = "in"
    label: str | None = None
    _name: str = field(default="", init=False, compare=False)

    def __set_name__(self, owner: type, name: str) -> None:
        object.__setattr__(self, "_name", name)

    @overload
    def __get__(self, obj: None, owner: type | None = None) -> PointDeclaration[P]: ...

    @overload
    def __get__(self, obj: object, owner: type | None = None) -> P: ...

    def __get__(self, obj: Any, owner: type | None = None) -> PointDeclaration[P] | P:
        return self if obj is None else cast(P, obj._named_points[self._name])

    def __set__(self, obj: object, value: object) -> None:
        raise AttributeError("named point references cannot be reassigned")

    def __post_init__(self) -> None:
        if self.count < 1:
            raise ValueError("a connection point declaration needs count >= 1")


# _port holds a PortHandle during authoring or a concrete Entity after hydration.
class PointRef:
    """Stable reference to one declared point on one equipment instance."""

    __slots__ = ("owner", "name", "_port")

    def __init__(self, owner: Any, name: str, port: Any) -> None:
        self.owner = owner
        self.name = name
        self._port = port

    @property
    def medium(self) -> Any:
        """Current medium hint for the referenced connection point."""
        return self._port.medium

    @medium.setter
    def medium(self, value: Any) -> None:
        self._port.medium = value

    @property
    def maps_to(self) -> Any:
        """The container's point this one stands for, as ``s223:mapsTo``."""
        return self._port.maps_to

    @maps_to.setter
    def maps_to(self, value: Any) -> None:
        self._port.maps_to = value

    def __repr__(self) -> str:
        return f"<PointRef {self.owner.name}.{self.name}>"

    def apply_properties(
        self, schema: PropertySchema, *, prefix: str | None = None
    ) -> PropertySet:
        """Attach values to this exact authored or hydrated point."""
        from .property_schema import apply_properties

        return apply_properties(self, schema, prefix=prefix)

    def quantity(
        self,
        name: str,
        value: float | QuantityAmount,
        *,
        kind: TermValue,
        unit: TermValue | None = None,
        capability: Literal["static", "observable", "actuatable"] = "static",
        label: str | None = None,
        **properties: Any,
    ) -> Entity:
        """Create a scalar property on this exact authored or hydrated point."""
        from plumb.qudt import _attached_quantity

        return _attached_quantity(
            self._port,
            name,
            value,
            unit=unit,
            kind=kind,
            capability=capability,
            label=label,
            **properties,
        )

    def sensor(
        self,
        name: str,
        *,
        kind: TermValue | EnumValue,
        unit: TermValue | None = None,
        sensor_class: type[Entity] | None = None,
        value: float | QuantityAmount | EnumValue | None = None,
        label: str | None = None,
        **properties: Any,
    ) -> Entity:
        """Add a sensor that observes a quantity here.

        Creates an observable ``<name>-value`` property of ``kind`` on this
        location and a sensor named ``name`` observing it. The sensor class
        is the most specific one for ``kind`` (``TurbidityMeter`` for
        Turbidity) unless ``sensor_class`` is given; ``properties`` such as
        ``of_medium`` go to the observed property.
        """
        from plumb.qudt import _attached_sensor

        return _attached_sensor(
            self._port,
            name,
            kind=kind,
            unit=unit,
            sensor_class=sensor_class,
            value=value,
            label=label,
            **properties,
        )


class PointGroupRef:
    """Stable reference to a declared interchangeable point group."""

    __slots__ = ("owner", "name", "points")

    def __init__(self, owner: Any, name: str, points: tuple[PointRef, ...]) -> None:
        self.owner = owner
        self.name = name
        self.points = points

    def __iter__(self):
        return iter(self.points)

    def __len__(self) -> int:
        return len(self.points)

    def __repr__(self) -> str:
        return f"<PointGroupRef {self.owner.name}.{self.name} x{len(self.points)}>"


def endpoint_owner(endpoint: Any) -> Any:
    """The equipment a connection endpoint belongs to.

    Ports and point references report their owner; a concrete connection
    point reports the entity that owns it; anything else is its own owner.
    """
    from .entity import Entity
    from .resolution import PortHandle

    owner = (
        endpoint.owner
        if isinstance(endpoint, (PortHandle, PointRef, PointGroupRef))
        else endpoint
    )
    if isinstance(owner, Entity):
        domain = owner.meta.registry._domain
        if domain is not None:
            return domain.owner(owner)
    return owner
