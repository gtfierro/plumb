"""Deferred connection intentions and immutable resolution results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterator, Literal

from .enums import _local
from .errors import ModelingError
from .points import PointRef, endpoint_owner
from .terms import TermValue

if TYPE_CHECKING:
    import rdflib

    from .entity import Entity
    from .enums import EnumValue
    from .model import Model
    from .property_schema import PropertySchema, PropertySet, QuantityAmount
    from .points import PointGroupRef


class PortHandle:
    """Stable authored name and constraints for a deferred connection point."""

    def __init__(
        self,
        model: Model,
        owner: Entity,
        name: str,
        direction: str | tuple[str, ...],
        *,
        medium: EnumValue | None = None,
        label: str | None = None,
        fixed_medium: bool = False,
    ) -> None:
        self._model = model
        self.owner = owner
        self.name = name
        self._direction = direction
        self._medium = medium
        self.label = label
        self._fixed_medium = fixed_medium
        self.symmetry_key: str | None = None
        self._paired_with: PortHandle | None = None
        self._maps_to: PortHandle | Entity | None = None
        self.roles: list[EnumValue] = []
        self._properties: list[Entity] = []
        self._boundary_systems: list[Entity] = []

    @property
    def direction(self) -> str | tuple[str, ...]:
        """The fixed direction or direction domain authored for this port."""
        return self._direction

    @property
    def medium(self) -> EnumValue | None:
        return self._medium

    @medium.setter
    def medium(self, value: EnumValue | None) -> None:
        self._model._assert_mutable()
        if self._fixed_medium and value != self._medium:
            raise ModelingError(f"{self.owner.name}.{self.name} medium is fixed")
        self._medium = value
        self._model._touch(self.owner)

    @property
    def paired_with(self) -> PortHandle | None:
        return self._paired_with

    def pair(self, other: PortHandle) -> PortHandle:
        """Pair two internal ports and constrain them to one medium."""
        if other._model is not self._model:
            raise ValueError("paired ports must belong to the same Model")
        self._model._assert_mutable()
        self._paired_with = other
        other._paired_with = self
        self._model._touch(self.owner, other.owner)
        return self

    @property
    def maps_to(self) -> PortHandle | Entity | None:
        """The container's point this port stands for, as ``s223:mapsTo``.

        The target may be another port or a concrete point. Resolution gives
        both the same medium and writes the link onto the concrete points.
        """
        return self._maps_to

    @maps_to.setter
    def maps_to(self, value: PortHandle | PointRef | Entity | None) -> None:
        self._model._assert_mutable()
        if isinstance(value, PointRef):
            value = value._port
        if value is not None:
            from .lifecycle import require_domain

            require_domain(self.owner).check_mapping(self, value)
        previous = self._maps_to
        self._maps_to = value
        owners = [self.owner]
        for target in (previous, value):
            if target is not None:
                owners.append(endpoint_owner(target))
        self._model._touch(*owners)

    def quantity(
        self,
        name: str,
        value: float | QuantityAmount,
        *,
        unit: TermValue | None = None,
        kind: TermValue,
        capability: Literal["static", "observable", "actuatable"] = "static",
        label: str | None = None,
        **properties: Any,
    ) -> Entity:
        """Attach a quantity to the connection point created for this port."""
        from plumb.qudt import _attached_quantity

        return _attached_quantity(
            self,
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
            self,
            name,
            kind=kind,
            unit=unit,
            sensor_class=sensor_class,
            value=value,
            label=label,
            **properties,
        )

    def apply_properties(
        self, schema: PropertySchema, *, prefix: str | None = None
    ) -> PropertySet:
        """Attach a generated property schema to this port's concrete point."""
        from .property_schema import apply_properties

        return apply_properties(self, schema, prefix=prefix)

    def __repr__(self) -> str:
        return f"<PortHandle {self.owner.name}.{self.name}>"


class ConnectionHandle:
    """Stable, editable reference to a deferred connection intention.

    Generated Connection properties are staged on the handle before
    resolution. Multi-valued properties expose a small set-like proxy, so
    ``handle.has_role.add(role)`` mirrors authored entity relationships.
    """

    _OWN_ATTRIBUTES = frozenset(
        {
            "identifier",
            "source",
            "target",
            "name",
            "medium",
            "connection_class",
            "label",
            "comment",
        }
    )

    def __init__(
        self,
        model: Model,
        identifier: int,
        source: Entity | PortHandle | PointGroupRef,
        target: Entity | PortHandle | PointGroupRef,
        *,
        medium: EnumValue | None,
        connection: type[Entity] | None,
        name: str,
    ) -> None:
        self._model = model
        self.identifier = identifier
        self.source = source
        self.target = target
        self._medium = medium
        self._connection_class = connection
        self.name = name
        self._label = name
        self._comment: str | None = None
        self._assignments: dict[str, Any] = {}

    @property
    def medium(self) -> EnumValue | None:
        """The authored medium constraint, or ``None`` if unconstrained.

        Assignment invalidates cached resolution so the next check or resolve
        uses the new hint.
        """
        return self._medium

    @medium.setter
    def medium(self, value: EnumValue | None) -> None:
        self._model._assert_mutable()
        self._medium = value
        self._model._touch(self.source, self.target)

    @property
    def connection_class(self) -> type[Entity] | None:
        return self._connection_class

    @connection_class.setter
    def connection_class(self, value: type[Entity] | None) -> None:
        self._model._assert_mutable()
        self._connection_class = value
        self._model._touch(self.source, self.target)

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._model._assert_mutable()
        self._label = value
        self._model._touch(self.source, self.target)

    @property
    def comment(self) -> str | None:
        return self._comment

    @comment.setter
    def comment(self, value: str | None) -> None:
        self._model._assert_mutable()
        self._comment = value
        self._model._touch(self.source, self.target)

    def __getattr__(self, name: str) -> Any:
        """Expose generated Connection properties as staged values."""
        descriptor = self._connection_descriptor(name)
        if descriptor is None:
            raise AttributeError(f"{type(self).__name__!s} has no attribute {name!r}")
        if _is_many_descriptor(descriptor):
            return _StagedCollection(self, name)
        return self._assignments.get(name)

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
            self,
            name,
            kind=kind,
            unit=unit,
            sensor_class=sensor_class,
            value=value,
            label=label,
            **properties,
        )

    def apply_properties(
        self, schema: PropertySchema, *, prefix: str | None = None
    ) -> PropertySet:
        """Attach a generated schema to the eventual connection."""
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
        """Create a scalar property on the eventual connection."""
        from plumb.qudt import _attached_quantity

        return _attached_quantity(
            self,
            name,
            value,
            unit=unit,
            kind=kind,
            capability=capability,
            label=label,
            **properties,
        )

    def _connection_type(self) -> type[Entity]:
        if self._connection_class is not None:
            return self._connection_class
        from .lifecycle import require_domain

        return require_domain(endpoint_owner(self.source)).connection_type(self)

    def __setattr__(self, name: str, value: Any) -> None:
        """Stage assignment to a generated Connection property."""
        if (
            name.startswith("_")
            or name in self._OWN_ATTRIBUTES
            or "_model" not in self.__dict__
        ):
            object.__setattr__(self, name, value)
            return
        descriptor = self._connection_descriptor(name)
        if descriptor is None:
            object.__setattr__(self, name, value)
            return
        if _is_many_descriptor(descriptor):
            from .enums import EnumValue
            from .entity import Entity

            if isinstance(value, (EnumValue, Entity, TermValue, str, bytes)):
                raise TypeError(f"{name} is multi-valued; assign an iterable")
            try:
                value = list(value)
            except TypeError:
                raise TypeError(
                    f"{name} is multi-valued; assign an iterable or use "
                    f"handle.{name}.add(value)"
                ) from None
        self._stage(name, value)

    def assign(self, **properties: Any) -> ConnectionHandle:
        """Stage properties, including custom-subclass escape-hatch values."""
        for name, value in properties.items():
            descriptor = self._connection_descriptor(name)
            if descriptor is None:
                self._stage(name, value)
            else:
                setattr(self, name, value)
        return self

    def _connection_descriptor(self, name: str) -> object | None:
        connection_cls = self._connection_type()
        for cls in connection_cls.__mro__:
            if name in cls.__dict__:
                return cls.__dict__[name]
        return None

    def _stage(self, name: str, value: Any) -> None:
        self._model._assert_mutable()
        self._assignments[name] = value
        self._model._touch(self.source, self.target)

    def __repr__(self) -> str:
        return (
            f"<ConnectionHandle {self.name}: {self.source.name} -> {self.target.name}>"
        )


DeferredEndpoint = PortHandle | PointRef | ConnectionHandle
"""A not-yet-resolved connection point or connection.

Properties that name a location, such as a sensor's observation location,
accept one; resolution replaces it with the concrete entity.
"""


class _StagedCollection:
    """Live collection view over one multi-valued handle assignment."""

    def __init__(self, handle: ConnectionHandle, name: str) -> None:
        self._handle = handle
        self._name = name

    def add(self, *values: Any) -> None:
        """Append values, ignoring duplicates."""
        current = list(self._handle._assignments.get(self._name, ()))
        changed = False
        for value in values:
            if value not in current:
                current.append(value)
                changed = True
        if changed:
            self._handle._stage(self._name, current)

    def remove(self, value: Any) -> None:
        """Remove a staged value."""
        current = list(self._handle._assignments.get(self._name, ()))
        current.remove(value)
        self._handle._stage(self._name, current)

    def clear(self) -> None:
        """Remove all staged values."""
        if self._handle._assignments.get(self._name):
            self._handle._stage(self._name, [])

    def __iter__(self) -> Iterator[Any]:
        return iter(self._handle._assignments.get(self._name, ()))

    def __len__(self) -> int:
        return len(self._handle._assignments.get(self._name, ()))

    def __contains__(self, value: object) -> bool:
        return value in self._handle._assignments.get(self._name, ())

    def __repr__(self) -> str:
        values = list(self)
        return f"StagedCollection({self._name}={values!r})"


def _is_many_descriptor(descriptor: object) -> bool:
    from .relations import EnumSet, Rel

    return isinstance(descriptor, (EnumSet, Rel))


@dataclass(frozen=True)
class ResolutionIssue:
    """A solver diagnostic tied to authored object names when possible."""

    message: str
    labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolutionReport:
    """Non-materializing result returned by :meth:`Model.check`."""

    status: Literal["complete", "underconstrained", "unsatisfiable"]
    issues: tuple[ResolutionIssue, ...] = ()

    @property
    def satisfiable(self) -> bool:
        return self.status != "unsatisfiable"

    @property
    def complete(self) -> bool:
        return self.status == "complete"

    def __bool__(self) -> bool:
        return self.satisfiable


@dataclass(frozen=True)
class ResolutionExplanation:
    """Human-readable provenance for one materialized connection decision."""

    connection: str
    medium: EnumValue
    source_point: str
    target_point: str
    medium_reason: Literal[
        "explicit connection",
        "explicit port",
        "paired port",
        "ontology constraint",
        "affinity preference",
    ]
    evidence: tuple[str, ...] = ()

    def __str__(self) -> str:
        lines = [
            f"{self.connection}: {self.source_point} -> {self.target_point}",
            f"  medium: {_local(self.medium.iri)} ({self.medium_reason})",
        ]
        lines.extend(f"  - {line}" for line in self.evidence)
        return "\n".join(lines)

    def _repr_pretty_(self, printer: Any, cycle: bool) -> None:
        # IPython and Jupyter display the readable form; repr() keeps fields.
        printer.text(str(self))


class ResolvedModel:
    """Frozen concrete model produced from authored entities and intentions."""

    def __init__(
        self,
        model: Model,
        connections: dict[int, Entity],
        explanations: dict[int, ResolutionExplanation],
        source_revision: int,
        authored_model: Model | None = None,
    ) -> None:
        self._model = model
        self._authored_model = model if authored_model is None else authored_model
        self._connections = dict(connections)
        self._explanations = dict(explanations)
        self._source_revision = source_revision
        self._intent_endpoints = tuple(
            (
                handle.identifier,
                handle.source,
                handle.target,
                endpoint_owner(handle.source),
                endpoint_owner(handle.target),
            )
            for handle in self._authored_model._connection_intents
        )
        self._model._frozen = True

    @property
    def source_revision(self) -> int:
        """The authored revision captured by this immutable snapshot."""
        return self._source_revision

    @property
    def entities(self) -> tuple[Entity, ...]:
        return tuple(self._model.entities)

    def __getitem__(self, name: str) -> Any:
        return self._model[name]

    def __iter__(self):
        return iter(self._model)

    def __len__(self) -> int:
        return len(self._model)

    def find_all(self, entity_type: Any = None, /, **options: Any) -> list[Any]:
        """``Model.find_all`` over the concrete snapshot entities."""
        return self._model.find_all(entity_type, **options)

    def find(self, entity_type: Any = None, /, **options: Any) -> Any:
        """``Model.find`` over the concrete snapshot entities."""
        return self._model.find(entity_type, **options)

    def connection(self, handle: ConnectionHandle) -> Any:
        """Return the concrete connection corresponding to ``handle``."""
        if handle._model is not self._authored_model:
            raise KeyError("connection handle does not belong to this snapshot")
        try:
            return self._connections[handle.identifier]
        except KeyError:
            raise KeyError(
                "connection handle does not belong to this snapshot"
            ) from None

    def point(self, reference: Any) -> Any:
        """Resolve a named point reference to its concrete snapshot point."""
        from .points import PointGroupRef, PointRef
        from .entity import Entity

        if isinstance(reference, PointGroupRef):
            return tuple(self.point(item) for item in reference.points)
        if not isinstance(reference, PointRef):
            raise TypeError("point() expects a PointRef or PointGroupRef")
        if reference.owner.meta.model not in (self._authored_model, self._model):
            raise KeyError("point reference does not belong to this snapshot")
        owner = self._model[reference.owner.name]
        if isinstance(reference._port, Entity):
            return self._model[reference._port.name]
        for point in getattr(owner, "has_connection_point"):
            if point.name == reference._port.name:
                return point
        raise KeyError(
            f"point {reference.owner.name}.{reference.name} was not resolved"
        )

    def explain(
        self,
        handle: ConnectionHandle | Entity | PortHandle,
        target: Entity | PortHandle | Any | None = None,
    ) -> ResolutionExplanation:
        """Explain a connection by handle or by its authored endpoints.

        Passing both endpoints also works for links authored with ``>>``,
        whose operator result does not expose the internal connection handle.
        """
        if not isinstance(handle, ConnectionHandle):
            if target is None:
                raise TypeError("explain() needs a handle or both connection endpoints")
            from .points import PointRef, endpoint_owner

            source = handle._port if isinstance(handle, PointRef) else handle
            destination = target._port if isinstance(target, PointRef) else target
            intents = self._intent_endpoints
            # The exact endpoints pick out one connection among several
            # between the same equipment; otherwise match by owner, as the
            # solver groups connections.
            matches = [
                candidate
                for candidate in intents
                if candidate[1] is source and candidate[2] is destination
            ]
            source_owner = endpoint_owner(source)
            target_owner = endpoint_owner(destination)
            if not matches:
                matches = [
                    candidate
                    for candidate in intents
                    if candidate[3] is source_owner and candidate[4] is target_owner
                ]
            if len(matches) != 1:
                raise KeyError(
                    f"expected one authored connection from {source_owner.name} "
                    f"to {target_owner.name}, found {len(matches)}"
                )
            identifier = matches[0][0]
        else:
            if handle._model is not self._authored_model:
                raise KeyError("connection handle does not belong to this snapshot")
            identifier = handle.identifier
        try:
            return self._explanations[identifier]
        except KeyError:
            raise KeyError(
                "connection handle does not belong to this snapshot"
            ) from None

    def graph(self) -> rdflib.Graph:
        if self._model._loaded_graph is not None:
            return self._model.graph()
        return self._model._graph_unresolved()
