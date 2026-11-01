"""Internal S223 capabilities shared by S223 and WaTr authoring packages.

Vocabulary interpretation lives here; callers keep the ordinary Model and
Entity interfaces. Native planning is imported only for deferred intentions.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING, Any

from .core.errors import ModelingError

if TYPE_CHECKING:
    from .core import Entity, Model, EnumValue, PortHandle, ConnectionHandle
    from .core.lifecycle import Plan
    from .core.traversal import Direction, Hop

S223 = "http://data.ashrae.org/standard223#"


def point_direction(cls: type[Entity]) -> str | None:
    """Read semantic point ancestry, independently of Python MRO repair."""
    directions = {
        direction
        for name, direction in (
            ("BidirectionalConnectionPoint", "bi"),
            ("InletConnectionPoint", "in"),
            ("OutletConnectionPoint", "out"),
        )
        if cls.meta.is_a(S223 + name)
    }
    if len(directions) > 1:
        raise ModelingError(f"{cls.meta.iri}: ambiguous point direction")
    if directions:
        return directions.pop()
    return "bi" if cls.meta.is_a(S223 + "ConnectionPoint") else None


class _S223Domain:
    def plan(self, model: Model) -> Plan | None:
        # Loaded RDF already states concrete topology. Replanning would invent
        # facts and turn a read/copy operation into an authoring operation. Keep
        # the solver import below this gate so neither loaded graphs nor plain
        # concrete models need Z3 merely to serialize or freeze their state.
        if model._loaded_graph is not None or not (
            model._connection_intents or model._port_intents
        ):
            return None
        from .solver223 import plan_model

        return plan_model(model)

    def initialize(self, entity: Entity) -> None:
        m = entity.meta.model
        declarations = type(entity)._point_declarations
        if declarations:
            from .core.points import PointGroupRef, PointRef

            for point_name, declaration in declarations.items():
                refs = []
                for index in range(declaration.count):
                    local = (
                        point_name
                        if declaration.count == 1
                        else f"{point_name}-{index + 1}"
                    )
                    port = m._defer_port(
                        entity,
                        f"{entity.name}-{local}",
                        declaration.direction,
                        medium=declaration.medium,
                        label=declaration.label,
                        fixed_medium=True,
                    )
                    # Group members are alternatives of the same named role.
                    # The planner may permute them without reporting ambiguity;
                    # differently named groups must remain distinct choices.
                    port.symmetry_key = point_name
                    refs.append(PointRef(entity, local, port))
                entity._named_points[point_name] = (
                    refs[0]
                    if len(refs) == 1
                    else PointGroupRef(entity, point_name, tuple(refs))
                )

    def restore(self, entity: Entity, *, strict: bool) -> None:
        if type(entity)._point_declarations:
            restore_named_points(
                entity, type(entity)._point_declarations, strict=strict
            )

    def finish_snapshot(self, model: Model) -> None:
        if model._loaded_graph is not None:
            return
        from .core import EnumValue

        for entity in model:
            if entity.meta.registry._domain is not self:
                continue
            medium = getattr(entity, "medium", None)
            if not isinstance(medium, EnumValue):
                continue
            for prop in getattr(entity, "has_property", ()):
                if hasattr(type(prop), "of_medium") and prop.of_medium is None:
                    prop.of_medium = medium
        for entity in model:
            if entity.meta.registry._domain is self:
                self.restore(entity, strict=True)

    def boundary(self, entity: Entity, points: tuple[Any, ...]) -> None:
        if not hasattr(entity, "has_boundary_connection_point"):
            raise TypeError(
                f"{type(entity).__name__} has no boundary connection points"
            )
        from .core.resolution import PortHandle
        from .core.points import PointRef

        entity._model._assert_mutable()
        boundary_points = getattr(entity, "has_boundary_connection_point")
        for point in points:
            if isinstance(point, PointRef):
                point = point._port
            if isinstance(point, PortHandle):
                if point._model is not entity._model:
                    raise ValueError("boundary port must belong to the same Model")
                if entity not in point._boundary_systems:
                    point._boundary_systems.append(entity)
                    entity._model._touch(entity, point.owner)
            else:
                boundary_points.add(point)

    def port(
        self,
        entity: Entity,
        name: str,
        *,
        direction: str,
        medium: EnumValue | None,
        label: str | None,
    ) -> PortHandle:
        if not entity.meta.is_a(S223 + "Connectable"):
            raise TypeError(f"{type(entity).__name__} has no connection points")
        return entity.meta.model._defer_port(
            entity, name, direction, medium=medium, label=label
        )

    def ports(self, entity: Entity) -> tuple[Entity | PortHandle, ...]:
        return tuple(getattr(entity, "has_connection_point", ())) + tuple(
            port for port in entity.meta.model._port_intents if port.owner is entity
        )

    def connection_type(self, handle: ConnectionHandle) -> type[Entity]:
        from .core import Registry
        from .core.points import endpoint_owner

        registry = Registry.for_entities(
            [endpoint_owner(handle.source), endpoint_owner(handle.target)],
            values=[handle.medium],
        )
        return registry.by_iri[S223 + "Connection"]

    def check_mapping(self, port: PortHandle, target: object) -> None:
        from .core import Entity, PortHandle
        from .core.points import endpoint_owner

        if not isinstance(target, PortHandle) and not (
            isinstance(target, Entity) and target.meta.is_a(S223 + "ConnectionPoint")
        ):
            raise TypeError(
                f"{port.owner.name}.{port.name}.maps_to takes a port or connection point, got {type(target).__name__}"
            )
        if target._model is not port._model:
            raise ValueError(
                f"{port.owner.name}.{port.name}.maps_to: target belongs to another Model"
            )
        if target is port or endpoint_owner(target) is port.owner:
            raise ModelingError(
                f"{port.owner.name}.{port.name} cannot map to a point of its own equipment; maps_to names a point of the containing equipment"
            )

    def create_system(
        self, model: Model, name: str, label: str | None, candidates: list[Entity]
    ) -> Entity:
        from .core import Registry

        members = tuple(
            entity
            for entity in candidates
            if entity.meta.is_a(S223 + "Connectable")
            or entity.meta.is_a(S223 + "System")
        )
        if not members:
            raise ModelingError(f"system {name!r} has no equipment members")
        registry = Registry.for_entities(members)
        system_cls = registry.by_iri[S223 + "System"]
        system = system_cls(name, label=label, has_member=members, model=model)
        model._system_intents.append((system, members))
        return system

    def owner(self, entity: Entity) -> Entity:
        if entity.meta.is_a(S223 + "ConnectionPoint"):
            return getattr(entity, "owner", None) or entity
        return entity

    def walk(
        self, start: Entity, direction: Direction, **options: Any
    ) -> Iterator[Hop]:
        from .topology223 import walk

        return walk(start, direction, **options)


S223_DOMAIN = _S223Domain()


def restore_named_points(
    entity: Entity, declarations: Mapping[str, Any], *, strict: bool
) -> None:
    """Rebuild generated references from RDF-observable point facts."""
    from .core.points import PointGroupRef, PointRef

    # Names minted by one Python run are not an RDF identification contract.
    # Recover references from the declared direction, medium, label, and count.
    # Consume each matched point once so two declarations cannot silently bind
    # to the same RDF resource. In strict mode an ambiguous match must fail.
    candidates = list(getattr(entity, "has_connection_point"))
    used: set[Entity] = set()
    direction_classes = {
        "in": "InletConnectionPoint",
        "out": "OutletConnectionPoint",
        "bi": "BidirectionalConnectionPoint",
    }
    for name, declaration in declarations.items():
        direction = direction_classes[declaration.direction]
        medium = declaration.medium
        label = declaration.label
        matching = [
            point
            for point in candidates
            if point not in used
            and point.meta.is_a(S223 + direction)
            and (
                medium is None
                or getattr(point, "medium", None) is not None
                and getattr(point, "medium").iri == medium.iri
            )
            and (label is None or point.label == label)
        ]
        if len(matching) != declaration.count:
            if strict and (matching or declaration.count):
                raise ModelingError(
                    f"cannot identify named point {entity.name}.{name} uniquely "
                    f"from RDF facts (expected {declaration.count}, found {len(matching)})"
                )
            continue
        used.update(matching)
        refs = tuple(
            PointRef(
                entity, name if declaration.count == 1 else f"{name}-{index + 1}", point
            )
            for index, point in enumerate(
                sorted(matching, key=lambda point: point.name)
            )
        )
        entity._named_points[name] = (
            refs[0] if len(refs) == 1 else PointGroupRef(entity, name, refs)
        )
