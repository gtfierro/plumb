"""S223 topology interpretation and walks, shared by canonical and water views."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast

from .core.entity import Entity
from .domain223 import point_direction
from .core.errors import ModelingError
from .core.traversal import Crossing, Direction, Hop, _index, _order, _sorted, matches

if TYPE_CHECKING:
    from .core.model import Model

_S223 = "http://data.ashrae.org/standard223#"
_HAS_POINT = {_S223 + "hasConnectionPoint", _S223 + "hasOptionalConnectionPoint"}
_POINT_OF = _S223 + "isConnectionPointOf"
_THROUGH = _S223 + "connectsThrough"
_AT = _S223 + "connectsAt"
_MAPS_TO = _S223 + "mapsTo"
_BOUNDARY = _S223 + "hasBoundaryConnectionPoint"
_MEMBER = _S223 + "hasMember"
_EXITS = {"downstream": {"out", "bi"}, "upstream": {"in", "bi"}}
_ENTRIES = {"downstream": {"in", "bi"}, "upstream": {"out", "bi"}}


@dataclass
class _Topology:
    order: dict[Entity, int]
    direction: dict[Entity, str] = field(default_factory=dict)
    owner: dict[Entity, Entity] = field(default_factory=dict)
    points: dict[Entity, list[Entity]] = field(default_factory=dict)
    connections: dict[Entity, list[Entity]] = field(default_factory=dict)
    on_connection: dict[Entity, list[Entity]] = field(default_factory=dict)
    maps_to: dict[Entity, list[Entity]] = field(default_factory=dict)
    mapped_from: dict[Entity, list[Entity]] = field(default_factory=dict)
    boundary: dict[Entity, list[Entity]] = field(default_factory=dict)
    boundary_of: dict[Entity, list[Entity]] = field(default_factory=dict)
    direct_members: dict[Entity, list[Entity]] = field(default_factory=dict)
    _members: dict[Entity, frozenset[Entity]] = field(default_factory=dict)

    def members(self, system: Entity) -> frozenset[Entity]:
        """Members of ``system`` at any depth of nested systems."""
        cached = self._members.get(system)
        if cached is None:
            found: set[Entity] = set()
            stack = list(self.direct_members.get(system, ()))
            while stack:
                item = stack.pop()
                if item not in found:
                    found.add(item)
                    stack.extend(self.direct_members.get(item, ()))
            cached = self._members[system] = frozenset(found)
        return cached


def _build_topology(model: Model) -> _Topology:
    # Build both directions of each conceptual link even when the loaded graph
    # asserts only one RDF predicate (connectsAt or connectsThrough, for example).
    # Deduplicate before sorting by model order: inverse assertions must neither
    # duplicate a hop nor let RDF iteration order choose the reported path.
    order = _order(model)
    topology = _Topology(order)
    links: defaultdict[str, defaultdict[Entity, dict[Entity, None]]] = defaultdict(
        lambda: defaultdict(dict)
    )

    def add(kind: str, key: Entity, value: Entity) -> None:
        links[kind][key][value] = None

    for entity in model.entities:
        direction = point_direction(type(entity))
        if direction is not None:
            topology.direction[entity] = direction
        for spec, value in entity._property_values():
            if not isinstance(value, Entity):
                continue
            predicate = spec.predicate
            if predicate in _HAS_POINT:
                topology.owner.setdefault(value, entity)
                add("points", entity, value)
            elif predicate == _POINT_OF:
                topology.owner.setdefault(entity, value)
                add("points", value, entity)
            elif predicate == _THROUGH:
                add("connections", entity, value)
                add("on_connection", value, entity)
            elif predicate == _AT:
                add("on_connection", entity, value)
                add("connections", value, entity)
            elif predicate == _MAPS_TO:
                add("maps_to", entity, value)
                add("mapped_from", value, entity)
            elif predicate == _BOUNDARY:
                add("boundary", entity, value)
                add("boundary_of", value, entity)
            elif predicate == _MEMBER:
                add("direct_members", entity, value)
    for kind, mapping in links.items():
        setattr(
            topology,
            kind,
            {key: _sorted(values, order) for key, values in mapping.items()},
        )
    return topology


def walk(
    start: Entity,
    direction: Direction = "downstream",
    *,
    through: Mapping[str, object] | Callable[[Crossing], object] | None = None,
    descend: bool = False,
    include_connections: bool = False,
    max_hops: int | None = None,
) -> Iterator[Hop]:
    """Breadth-first walk of the connection graph from ``start``."""
    if direction not in _EXITS:
        raise ValueError("direction must be 'downstream' or 'upstream'")
    if max_hops is not None and max_hops < 0:
        raise ValueError("max_hops must be non-negative")
    model = start.meta.model
    if not model._frozen and (model._connection_intents or model._port_intents):
        raise ModelingError(
            "this model has connections that are not resolved yet; walk the "
            "resolved snapshot instead: model.resolve()[name].walk(...)"
        )
    return _Walk(
        _index(model, "topology", _build_topology),
        direction,
        through,
        descend=descend,
        include_connections=include_connections,
        max_hops=max_hops,
    ).run(start)


#: A pending step: ("exit", point) leaves through a point; ("enter", point,
#: inner) steps through ``maps_to`` from a container point to an inner one.
_Step = tuple[str, Entity, Entity | None, tuple[Crossing, ...]]


class _Walk:
    def __init__(
        self,
        topology: _Topology,
        direction: Direction,
        through: Mapping[str, object] | Callable[[Crossing], object] | None,
        *,
        descend: bool,
        include_connections: bool,
        max_hops: int | None,
    ) -> None:
        self.topology = topology
        self.exits = _EXITS[direction]
        self.entries = _ENTRIES[direction]
        self.filters: Mapping[str, object] | None = None
        self.predicate: Callable[[Crossing], object] | None = None
        if isinstance(through, Mapping):
            self.filters = cast(Mapping[str, object], through)
        else:
            self.predicate = through
        self.descend = descend
        self.include_connections = include_connections
        self.max_hops = max_hops
        # These sets have different jobs: reached suppresses duplicate results,
        # while entered/left bound point traversal. Reaching equipment through
        # one inlet must not prevent exploring its other points or its mapsTo
        # boundaries; one visited set for everything would lose valid paths.
        self.left: set[Entity] = set()
        self.entered: set[Entity] = set()
        self.reached: set[Entity] = set()

    def run(self, start: Entity) -> Iterator[Hop]:
        if self.max_hops == 0:
            return
        topology = self.topology
        self.reached.add(start)
        steps: list[_Step] = []
        hops: list[Hop] = []
        if start in topology.direction:
            if topology.direction[start] in self.exits:
                steps.append(("exit", start, None, ()))
            else:
                self.entered.add(start)
                steps.extend(self._through(start, ()))
        elif start in topology.on_connection:
            for point in topology.on_connection[start]:
                if topology.direction.get(point) in self.entries:
                    self._cross(Crossing(None, start, point), (), 1, hops, steps)
        else:
            points = topology.boundary.get(start) or topology.points.get(start, ())
            steps.extend(
                ("exit", point, None, ())
                for point in points
                if topology.direction.get(point) in self.exits
            )
        depth = 1
        if hops:
            yield from self._ordered(hops)
            depth = 2
        while steps and (self.max_hops is None or depth <= self.max_hops):
            hops = []
            following: list[_Step] = []
            for kind, point, inner, via in sorted(
                steps, key=lambda step: topology.order.get(step[2] or step[1], 0)
            ):
                if kind == "exit":
                    if point in self.left:
                        continue
                    self.left.add(point)
                    self._leave(point, via, depth, hops, following)
                elif inner is not None:
                    self._cross(
                        Crossing(point, None, inner), via, depth, hops, following
                    )
            yield from self._ordered(hops)
            steps = following
            depth += 1

    def _ordered(self, hops: list[Hop]) -> list[Hop]:
        order = self.topology.order
        return sorted(hops, key=lambda hop: order.get(hop.entity, len(order)))

    def _allowed(self, crossing: Crossing) -> bool:
        if self.predicate is not None:
            return bool(self.predicate(crossing))
        if self.filters is None or crossing.connection is None:
            return True
        return matches(crossing.connection, self.filters)

    def _leave(
        self,
        point: Entity,
        via: tuple[Crossing, ...],
        depth: int,
        hops: list[Hop],
        following: list[_Step],
    ) -> None:
        topology = self.topology
        for connection in topology.connections.get(point, ()):
            for other in topology.on_connection.get(connection, ()):
                if other is point or topology.direction.get(other) not in self.entries:
                    continue
                self._cross(
                    Crossing(point, connection, other), via, depth, hops, following
                )
        for outer in topology.maps_to.get(point, ()):
            crossing = Crossing(point, None, outer)
            if self._allowed(crossing):
                following.append(("exit", outer, None, via + (crossing,)))

    def _cross(
        self,
        crossing: Crossing,
        via: tuple[Crossing, ...],
        depth: int,
        hops: list[Hop],
        following: list[_Step],
    ) -> None:
        if not self._allowed(crossing):
            return
        path = via + (crossing,)
        connection = crossing.connection
        if (
            self.include_connections
            and connection is not None
            and connection not in self.reached
        ):
            self.reached.add(connection)
            hops.append(Hop(connection, depth, path))
        point = crossing.entry
        if point in self.entered:
            return
        self.entered.add(point)
        topology = self.topology
        owner = topology.owner.get(point)
        if owner is not None:
            self._reach(owner, depth, path, hops)
        previous = topology.owner.get(crossing.exit) if crossing.exit else None
        for system in topology.boundary_of.get(point, ()):
            if previous is None or previous not in topology.members(system):
                self._reach(system, depth, path, hops)
        following.extend(self._through(point, path))

    def _reach(
        self, entity: Entity, depth: int, path: tuple[Crossing, ...], hops: list[Hop]
    ) -> None:
        if entity not in self.reached:
            self.reached.add(entity)
            hops.append(Hop(entity, depth, path))

    def _through(self, point: Entity, path: tuple[Crossing, ...]) -> list[_Step]:
        """Continue from an entry point: past its owner, and with ``descend``
        also into the container through the points mapped to it.

        Passing through even when descending keeps ``descend=True`` a strict
        superset of ``descend=False``, at the same depths, however complete
        the container's internal model is.
        """
        topology = self.topology
        steps: list[_Step] = []
        if self.descend:
            steps.extend(
                ("enter", point, item, path)
                for item in topology.mapped_from.get(point, ())
            )
        owner = topology.owner.get(point)
        if owner is not None:
            steps.extend(
                ("exit", other, None, path)
                for other in topology.points.get(owner, ())
                if other is not point and topology.direction.get(other) in self.exits
            )
        return steps
