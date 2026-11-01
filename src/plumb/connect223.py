"""Deferred 223-style connection intentions.

Generated classes eagerly create only connection points whose shape fixes a
single medium. ``connect(a, b)`` records an intention; ``Model.resolve()`` (or
``graph()``, ``save()``, and ``validate()``) delegates layout, medium, point,
and Connection-subclass selection to the Z3 planner. Derived objects live in
an immutable resolved snapshot, leaving the authored model unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeGuard

from .core import ConnectionHandle, EnumValue, PortHandle
from .core.errors import ModelingError
from .core.points import PointGroupRef, PointRef, endpoint_owner
from .core import containment as _containment
from .core.meta import _port_requirements

if TYPE_CHECKING:
    from .core import Entity, Registry

S223 = "http://data.ashrae.org/standard223#"


class S223Connector:
    """Negotiates ``a >> b`` for a generated 223-style package.

    One instance per generated package, installed on the ``Connectable``
    root as ``_CONNECTOR`` by overlay code the emitter writes.
    """

    def __init__(
        self,
        registry: Registry,
        connection_classes: dict[str, str] | None = None,
    ) -> None:
        self.registry = registry
        #: medium IRI (or ancestor) -> Connection subclass python name
        self.connection_classes = connection_classes or {}

    # -- public entry points ---------------------------------------------

    def on_create(self, entity: Entity) -> None:
        """Materialize shape-required connection points on a new entity.

        A fresh ``Fan()`` immediately owns its air inlet and outlet — the
        shapes say they must exist whether or not anything is connected yet.
        Slots without a medium (e.g. Pump) stay lazy: a ConnectionPoint
        needs a medium, which only negotiation or the user can supply.
        """
        # This is only eager materialization of already determined facts, not
        # negotiation. Defer any choice of domain member or layout to the
        # planner, where neighboring intentions can contribute evidence.
        with _containment.suppressed():
            existing = list(getattr(entity, "has_connection_point"))
            for slot in _port_requirements(type(entity))[0]:
                if slot.medium is None:
                    continue
                slot_cls = self.registry.resolve(slot.cp_class)
                medium = self.registry.resolve_enum(slot.medium)
                # A shape class with enum descendants is a domain, not one
                # exact value. Leave those points for the solver so adjacent
                # intentions can select Water, Sludge, etc. WaTr commonly
                # constrains equipment to the broad Mix-Fluid domain.
                if any(
                    value.parent is medium
                    for value in self.registry.enums_by_iri.values()
                ):
                    continue
                already = sum(
                    1
                    for cp in existing
                    if cp.meta.is_a(slot_cls)
                    and getattr(cp, "medium") is not None
                    and getattr(cp, "medium").is_a(medium)
                )
                already += sum(
                    1
                    for port in entity.meta.model._port_intents
                    if port.owner is entity
                    and slot.direction
                    in (
                        (port.direction,)
                        if isinstance(port.direction, str)
                        else port.direction
                    )
                    and port.medium is not None
                    and port.medium.is_a(medium)
                    and (slot.label is None or port.label == slot.label)
                )
                model = entity.meta.model
                for _ in range(max(slot.min_count - already, 0)):
                    cp = slot_cls(
                        model._unique_name(f"{entity.name}-{slot.direction}"),
                        medium=medium,
                        owner=entity,
                        model=model,
                    )
                    # Points made here are interchangeable until connected
                    # or labelled; the solver must not treat them as choices.
                    cp._from_shape = True
                    existing.append(cp)

    def connect(
        self,
        a: Entity | PortHandle | PointRef | PointGroupRef,
        b: Entity | PortHandle | PointRef | PointGroupRef,
        *,
        medium: EnumValue | None = None,
        connection: type[Entity] | None = None,
        name: str | None = None,
        ports: Literal["match", "new"] = "match",
    ) -> ConnectionHandle:
        """Record a deferred connection intention and return its handle.

        With ``ports="new"``, bare equipment endpoints first get a fresh
        directed port each (``<name>-out`` / ``<name>-in``), so the
        connection never reuses an existing point.
        """
        if isinstance(a, PointRef):
            a = a._port
        if isinstance(b, PointRef):
            b = b._port
        model = endpoint_owner(a).meta.model
        if ports == "match" or not (_is_equipment(a) or _is_equipment(b)):
            return model._defer_connection(
                a, b, medium=medium, connection=connection, name=name
            )
        if endpoint_owner(b).meta.model is not model:
            raise ModelingError("connection endpoints must belong to the same Model")
        # Refuse before allocating ports, so the error names the connection
        # rather than a port and a loaded graph is not snapshotted for nothing.
        model._assert_accepts_connections()
        with model._atomic():
            if _is_equipment(a):
                a = self._new_port(a, "out", medium)
            if _is_equipment(b):
                b = self._new_port(b, "in", medium)
            return model._defer_connection(
                a, b, medium=medium, connection=connection, name=name
            )

    def _new_port(
        self, entity: Entity, direction: str, medium: EnumValue | None
    ) -> PortHandle:
        """Declare one more port on ``entity`` unless its shapes forbid it."""
        maximum = type(entity)._shape_max_ports
        if maximum is not None and len(entity.ports) >= maximum:
            raise ModelingError(f"{entity.name}: shape prohibits additional ports")
        name = entity.meta.model._unique_name(f"{entity.name}-{direction}")
        return entity.port(name, direction=direction, medium=medium)


def _is_equipment(endpoint: object) -> TypeGuard[Entity]:
    """A bare entity that owns connection points (not a port or point)."""
    from .core.entity import Entity

    return isinstance(endpoint, Entity) and hasattr(endpoint, "has_connection_point")
