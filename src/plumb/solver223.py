"""Deferred, finite-domain Z3 planner for S223 connection intentions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable

import z3

from .core import (
    AmbiguousModelError,
    CPConstraint,
    CPSlot,
    ConnectionHandle,
    ModelingError,
    PortHandle,
    ResolutionIssue,
    ResolutionExplanation,
    ResolutionReport,
    ResolvedModel,
    Registry,
    UnsatisfiableModelError,
)
from .core.enums import _local
from .core.snapshot import Snapshot

if TYPE_CHECKING:
    from .connect223 import S223Connector
    from .core import Entity, EnumValue, Model
    from .core.points import PointGroupRef


@dataclass
class _Point:
    owner: Entity
    cls: type[Entity]
    name: str
    active: z3.BoolRef
    medium: z3.IntNumRef | z3.ArithRef
    existing: Entity | None = None
    authored: PortHandle | None = None


@dataclass(frozen=True)
class _PointResult:
    owner: Entity
    cls: type[Entity]
    name: str
    medium: EnumValue
    existing: Entity | None
    authored: PortHandle | None = None


@dataclass(frozen=True)
class _IntentResult:
    handle: ConnectionHandle
    source: _PointResult
    target: _PointResult
    medium: EnumValue
    connection_class: type[Entity]


@dataclass(frozen=True)
class _Plan:
    points: tuple[_PointResult, ...]
    intents: tuple[_IntentResult, ...]


@dataclass
class _ComponentResult:
    report: ResolutionReport
    plan: _Plan | None


def check_model(model: Model) -> ResolutionReport:
    """Check all deferred components without constructing a snapshot."""
    reports = [
        _solve_cached(model, handles, standalone).report
        for handles, standalone in _components(model)
    ]
    if any(report.status == "unsatisfiable" for report in reports):
        issues = tuple(issue for report in reports for issue in report.issues)
        return ResolutionReport("unsatisfiable", issues)
    if any(report.status == "underconstrained" for report in reports):
        issues = tuple(issue for report in reports for issue in report.issues)
        return ResolutionReport("underconstrained", issues)
    return ResolutionReport("complete")


def resolve_model(model: Model) -> ResolvedModel:
    """Solve all components and build a frozen concrete snapshot."""
    plans: list[_Plan] = []
    for handles, standalone in _components(model):
        result = _solve_cached(model, handles, standalone)
        if result.report.status == "unsatisfiable":
            labels = tuple(
                label for issue in result.report.issues for label in issue.labels
            )
            # Name the conflicting constraints; the bare issue text is generic.
            message = "; ".join(issue.message for issue in result.report.issues)
            raise UnsatisfiableModelError(
                f"{message}: {'; '.join(labels)}" if labels else message,
                core=labels,
            )
        if result.report.status == "underconstrained":
            raise AmbiguousModelError(
                "; ".join(issue.message for issue in result.report.issues),
                alternatives=tuple(issue.message for issue in result.report.issues),
            )
        assert result.plan is not None
        plans.append(result.plan)
    return _materialize(model, plans)


def _solve_cached(
    model: Model, handles: list[ConnectionHandle], standalone: set[Entity] | None = None
) -> _ComponentResult:
    """Reuse plans for unchanged sparse components across authored edits."""
    standalone = standalone or set()
    key = _component_key(handles, standalone)
    cached = model._component_cache.get(key)
    if cached is not None:
        return cached
    result = _solve_component(handles, materialize=True, standalone=standalone)
    # Bound stale plans retained during long interactive authoring sessions.
    if len(model._component_cache) >= 256:
        model._component_cache.pop(next(iter(model._component_cache)))
    model._component_cache[key] = result
    return result


def _component_key(
    handles: list[ConnectionHandle], standalone: set[Entity] | None = None
) -> tuple[Any, ...]:
    """Fingerprint the authored facts that affect one solver component."""
    endpoints = {
        endpoint
        for handle in handles
        for endpoint in (_owner(handle.source), _owner(handle.target))
    }
    endpoints.update(standalone or ())
    endpoint_facts: list[tuple[Any, ...]] = []
    for endpoint in sorted(endpoints, key=lambda entity: entity.name):
        points = []
        for point in getattr(endpoint, "has_connection_point"):
            medium = getattr(point, "medium")
            bound = getattr(point, "connection")
            points.append(
                (
                    point.name,
                    type(point).__name__,
                    medium.iri if medium is not None else None,
                    bound.name if bound is not None else None,
                    _mapping_name(_mapped(point)),
                    _property_media_key(getattr(point, "has_property", ())),
                )
            )
        for port in endpoint.meta.model._port_intents:
            if port.owner is endpoint:
                points.append(
                    (
                        port.name,
                        f"deferred-{port.direction}",
                        port.medium.iri if port.medium is not None else None,
                        port.paired_with.name if port.paired_with is not None else None,
                        _mapping_name(port.maps_to),
                        _property_media_key(port._properties),
                    )
                )
        endpoint_facts.append(
            (endpoint.name, type(endpoint).__name__, tuple(sorted(points)))
        )
    intent_facts = tuple(
        (
            handle.identifier,
            handle.source.name,
            handle.target.name,
            handle.medium.iri if handle.medium is not None else None,
            handle.connection_class.__name__
            if handle.connection_class is not None
            else None,
            _property_media_key(handle._assignments.get("has_property", ())),
        )
        for handle in sorted(handles, key=lambda item: item.identifier)
    )
    return (intent_facts, tuple(endpoint_facts))


def _components(model: Model) -> list[tuple[list[ConnectionHandle], set[Entity]]]:
    """Partition intentions by shared endpoint for sparse-model scaling."""
    handles = list(model._connection_intents)
    mappings = _mappings(model)
    if not handles and not mappings:
        return [
            ([], {entity}) for entity in model.entities if _has_named_points(entity)
        ]
    parent: dict[Entity, Entity] = {}

    def find(entity: Entity) -> Entity:
        parent.setdefault(entity, entity)
        while parent[entity] is not entity:
            parent[entity] = parent[parent[entity]]
            entity = parent[entity]
        return entity

    def union(left: Entity, right: Entity) -> None:
        a, b = find(left), find(right)
        if a is not b:
            parent[b] = a

    for handle in handles:
        union(_owner(handle.source), _owner(handle.target))
    # A mapped port and its container's point share a medium, so the two
    # pieces of equipment are solved together.
    for source, target in mappings:
        union(_owner(source), _owner(target))
    groups: dict[Entity, tuple[list[ConnectionHandle], set[Entity]]] = {}
    for handle in handles:
        groups.setdefault(find(_owner(handle.source)), ([], set()))[0].append(handle)
    for source, target in mappings:
        for owner in (_owner(source), _owner(target)):
            groups.setdefault(find(owner), ([], set()))[1].add(owner)
    result = list(groups.values())
    connected = set(parent)
    result.extend(
        ([], {entity})
        for entity in model.entities
        if entity not in connected and _has_named_points(entity)
    )
    return result


def _mapped(point: Entity | PortHandle) -> Entity | PortHandle | None:
    """The point ``point`` maps to, a port before resolution or a point."""
    if isinstance(point, PortHandle):
        return point.maps_to
    return getattr(point, "maps_to", None)


def _point_sources(entity: Entity) -> list[Entity | PortHandle]:
    """The concrete points and authored ports of ``entity``."""
    sources: list[Entity | PortHandle] = list(getattr(entity, "has_connection_point"))
    sources.extend(
        port for port in entity.meta.model._port_intents if port.owner is entity
    )
    return sources


def _mappings(
    model: Model,
) -> list[tuple[Entity | PortHandle, Entity | PortHandle]]:
    """``maps_to`` links with a port on either side, which the solver joins."""
    sources: list[Entity | PortHandle] = list(model._port_intents)
    sources.extend(entity for entity in model.entities if _mapped(entity) is not None)
    result = []
    for source in sources:
        target = _mapped(source)
        if target is None:
            continue
        if isinstance(source, PortHandle) or isinstance(target, PortHandle):
            result.append((source, target))
    return result


def _mapping_name(point: Entity | PortHandle | None) -> str | None:
    if isinstance(point, PortHandle):
        return f"{point.owner.name}.{point.name}"
    return point.name if point is not None else None


def _has_named_points(entity: Entity) -> bool:
    return bool(type(entity)._point_declarations)


def _solve_component(
    handles: list[ConnectionHandle],
    *,
    materialize: bool,
    standalone: set[Entity] | None = None,
) -> _ComponentResult:
    entities = {_owner(endpoint) for h in handles for endpoint in (h.source, h.target)}
    entities.update(standalone or ())
    registry = Registry.for_entities(
        entities,
        values=[handle.medium for handle in handles]
        + [
            port.medium
            for entity in entities
            for port in entity.meta.model._port_intents
            if port.owner is entity
        ],
    )
    connector = registry.resolve("Connectable")._CONNECTOR
    assert connector is not None
    enum_values = _relevant_media(entities, handles)
    enum_ids = {value.iri: index for index, value in enumerate(enum_values)}
    by_id = {index: value for index, value in enumerate(enum_values)}
    solver = z3.Solver()
    points: list[_Point] = []
    labels: dict[str, str] = {}

    def tracked(expr: z3.BoolRef, label: str, message: str) -> None:
        token = z3.Bool(f"track_{len(labels)}")
        labels[token.decl().name()] = f"{label}: {message}"
        solver.assert_and_track(expr, token)

    incident: dict[Entity, dict[str, int]] = {
        entity: {
            "in": sum(_owner(h.target) is entity for h in handles),
            "out": sum(_owner(h.source) is entity for h in handles),
        }
        for entity in entities
    }
    # A container's shapes describe its own points, not the parts' points
    # mapped onto it: an AHU lists only air points, yet its chilled-water
    # inlet stands for a coil's. The part decides a mapped point's medium.
    mapped_targets = {
        _mapped(source)
        for entity in entities
        for source in _point_sources(entity)
        if _mapped(source) is not None
    }
    for entity in sorted(entities, key=lambda item: item.name):
        entity_points = _make_points(entity, incident[entity], enum_values)
        points.extend(entity_points)
        authored_groups: dict[PortHandle, list[z3.BoolRef]] = {}
        for point in entity_points:
            if point.authored is not None and isinstance(point.active, z3.BoolRef):
                authored_groups.setdefault(point.authored, []).append(point.active)
        for authored, alternatives in authored_groups.items():
            if len(alternatives) > 1:
                solver.add(
                    z3.PbEq([(alternative, 1) for alternative in alternatives], 1)
                )
        for point in entity_points:
            solver.add(point.medium >= 0, point.medium < len(enum_values))
            if point.existing is not None:
                solver.add(point.active)
            stated = _stated_medium(point)
            if stated is not None:
                # An explicit medium overrides the class's medium domain: a
                # Fan's shapes mention only air, but a declared power inlet
                # may carry electricity.
                if stated.iri in enum_ids:
                    tracked(
                        point.medium == enum_ids[stated.iri],
                        point.name,
                        ("explicit medium " if point.authored else "medium ")
                        + _local(stated.iri),
                    )
                continue
            if (point.authored or point.existing) in mapped_targets:
                continue
            roots = _point_roots(point)
            if roots:
                tracked(
                    z3.Implies(
                        point.active,
                        _medium_in_roots(point.medium, roots, enum_values, enum_ids),
                    ),
                    point.name,
                    f"{point.cls.__name__} medium must be one of "
                    + ", ".join(sorted(_local(root) for root in roots)),
                )
        for slot_index, slot in enumerate(_all_slots(type(entity))):
            tracked(
                _slot_expr(entity_points, slot, enum_values, enum_ids),
                entity.name,
                f"required connection-point slot {slot_index}",
            )
        maximum_ports = type(entity)._shape_max_ports
        if maximum_ports is not None:
            tracked(
                z3.Sum([z3.If(point.active, 1, 0) for point in entity_points])
                <= maximum_ports,
                entity.name,
                "shape maximum connection-point count",
            )
        for constraint_index, constraint in enumerate(_all_constraints(type(entity))):
            if _contains_opaque(constraint):
                continue
            tracked(
                _constraint_expr(entity_points, constraint, enum_values, enum_ids),
                entity.name,
                f"boolean connection layout {constraint_index}",
            )

    by_authored = {
        point.authored: point for point in points if point.authored is not None
    }
    by_existing = {
        point.existing: point for point in points if point.existing is not None
    }
    for point in points:
        paired = None
        if point.authored is not None:
            paired = point.authored.paired_with
            other = by_authored.get(paired)
        elif point.existing is not None:
            paired = getattr(point.existing, "paired_with", None)
            other = by_existing.get(paired)
        else:
            other = None
        if paired is not None and other is not None:
            solver.add(point.medium == other.medium)
    # A port and the container's point it maps to carry the same medium and
    # face the same way: an inlet stands for the container's inlet.
    alternatives: dict[Entity | PortHandle, list[_Point]] = {}
    for point in points:
        key = point.authored if point.authored is not None else point.existing
        if key is not None:
            alternatives.setdefault(key, []).append(point)
    for source, sides in alternatives.items():
        targets = alternatives.get(_mapped(source))
        if not targets:
            continue
        tracked(
            sides[0].medium == targets[0].medium,
            sides[0].name,
            f"maps to {targets[0].name}, so they carry the same medium",
        )
        for side in sides:
            for target in targets:
                if _direction_of(side.cls) != _direction_of(target.cls):
                    tracked(
                        z3.Not(z3.And(side.active, target.active)),
                        side.name,
                        f"maps to {target.name}, so they face the same way",
                    )

    point_selections: dict[tuple[int, int], z3.BoolRef] = {}
    intent_mediums: dict[int, z3.ArithRef] = {}
    for handle in handles:
        intent_medium = z3.Int(f"intent_{handle.identifier}_medium")
        intent_mediums[handle.identifier] = intent_medium
        solver.add(intent_medium >= 0, intent_medium < len(enum_values))
        if handle.medium is not None:
            tracked(
                intent_medium == enum_ids[handle.medium.iri],
                handle.name,
                f"explicit medium {handle.medium.iri.rsplit('#', 1)[-1]}",
            )
        source_candidates = _eligible(points, handle.source, "out")
        target_candidates = _eligible(points, handle.target, "in")
        for side, candidates in (
            ("source", source_candidates),
            ("target", target_candidates),
        ):
            choices: list[z3.BoolRef] = []
            for point in candidates:
                key = (handle.identifier, points.index(point))
                selected = z3.Bool(f"intent_{handle.identifier}_{side}_{len(choices)}")
                point_selections[key] = selected
                choices.append(selected)
                solver.add(z3.Implies(selected, point.active))
                solver.add(z3.Implies(selected, point.medium == intent_medium))
            tracked(
                z3.PbEq([(choice, 1) for choice in choices], 1)
                if choices
                else z3.BoolVal(False),
                handle.name,
                f"exactly one {side} connection point",
            )

    for index, point in enumerate(points):
        uses = [
            selected
            for (handle_id, point_index), selected in point_selections.items()
            if point_index == index
        ]
        bound = (
            point.existing is not None
            and getattr(point.existing, "connection") is not None
        )
        if uses:
            solver.add(z3.PbLe([(use, 1) for use in uses], 0 if bound else 1))

    for host, variable, active, properties in _property_hosts(
        points, handles, intent_mediums
    ):
        for prop in properties:
            stated = _of_medium(prop)
            if stated is None:
                continue
            compatible = [
                enum_ids[value.iri]
                for value in enum_values
                if value.compatible_with(stated)
            ]
            tracked(
                z3.Implies(active, z3.Or([variable == item for item in compatible])),
                prop.name,
                f"ofMedium {_local(stated.iri)} must be compatible with the "
                f"medium of {host}",
            )

    if solver.check() == z3.unsat:
        core = tuple(str(item) for item in solver.unsat_core())
        messages = tuple(labels.get(item, item) for item in core)
        return _ComponentResult(
            ResolutionReport(
                "unsatisfiable",
                (ResolutionIssue("connection constraints are inconsistent", messages),),
            ),
            None,
        )

    _minimize_active(solver, points)
    _minimize_expression(
        solver,
        _medium_affinity_penalty(entities, points, enum_values, enum_ids),
    )
    assert solver.check() == z3.sat
    assignment = solver.model()
    observables = _observable_expressions(
        entities, points, handles, point_selections, intent_mediums
    )
    values = [assignment.eval(expr, model_completion=True) for expr in observables]
    solver.push()
    solver.add(z3.Or([expr != value for expr, value in zip(observables, values)]))
    ambiguous = solver.check() == z3.sat
    differences: tuple[str, ...] = ()
    if ambiguous:
        alternate = solver.model()
        differences = tuple(
            f"{expr}={value}/{alternate.eval(expr, model_completion=True)}"
            for expr, value in zip(observables, values)
            if not z3.is_true(
                z3.simplify(value == alternate.eval(expr, model_completion=True))
            )
        )
    solver.pop()
    if ambiguous:
        names = ", ".join(handle.name for handle in handles) or ", ".join(
            sorted(entity.name for entity in entities)
        )
        return _ComponentResult(
            ResolutionReport(
                "underconstrained",
                (
                    ResolutionIssue(
                        f"connection or named point choices remain ambiguous: {names}; "
                        "fix a point direction or medium, or connect it to equipment "
                        "that determines the choice",
                        differences,
                    ),
                ),
            ),
            None,
        )
    if not materialize:
        return _ComponentResult(ResolutionReport("complete"), None)
    return _ComponentResult(
        ResolutionReport("complete"),
        _extract_plan(
            handles,
            points,
            point_selections,
            intent_mediums,
            assignment,
            by_id,
            connector,
        ),
    )


def _property_hosts(
    points: list[_Point],
    handles: list[ConnectionHandle],
    intent_mediums: dict[int, z3.ArithRef],
) -> Iterable[tuple[str, z3.ArithRef, z3.BoolRef, Iterable[Entity]]]:
    """Each solved medium with the properties attached to its host.

    223P requires a property's ``ofMedium`` to be compatible with the
    ``hasMedium`` of the entity it describes, so these properties constrain
    the medium the solver chooses.
    """
    for handle in handles:
        yield (
            handle.name,
            intent_mediums[handle.identifier],
            z3.BoolVal(True),
            handle._assignments.get("has_property", ()),
        )
    for point in points:
        if point.authored is not None:
            properties: Iterable[Entity] = point.authored._properties
        elif point.existing is not None:
            properties = getattr(point.existing, "has_property", ())
        else:
            continue
        yield point.name, point.medium, point.active, properties


def _of_medium(prop: Entity) -> EnumValue | None:
    return getattr(prop, "of_medium") if _has_of_medium(prop) else None


def _has_of_medium(prop: Entity) -> bool:
    return any("of_medium" in cls.__dict__ for cls in type(prop).__mro__)


def _property_media_key(properties: Iterable[Entity]) -> tuple[Any, ...]:
    return tuple(
        sorted(
            (prop.name, medium.iri if (medium := _of_medium(prop)) else None)
            for prop in properties
        )
    )


def _fill_property_media(snapshot: Model) -> None:
    """Give each property without ``ofMedium`` the medium of its host."""
    from .core import EnumValue

    for entity in snapshot.entities:
        medium = getattr(entity, "medium", None)
        if not isinstance(medium, EnumValue):
            continue
        for prop in getattr(entity, "has_property", ()):
            if _has_of_medium(prop) and getattr(prop, "of_medium") is None:
                setattr(prop, "of_medium", medium)


def _relevant_media(
    entities: Iterable[Entity], handles: Iterable[ConnectionHandle]
) -> list[EnumValue]:
    values: dict[str, EnumValue] = {}
    entities = tuple(entities)
    registry = Registry.compose(entity.meta.registry for entity in entities)
    roots: set[str] = set()
    for entity in entities:
        for slot in _all_slots(type(entity)) + _constraint_slots(type(entity)):
            roots.update(_slot_roots(slot))
        for cp in getattr(entity, "has_connection_point"):
            medium = getattr(cp, "medium")
            if medium is not None:
                values[medium.iri] = medium
        for port in entity.meta.model._port_intents:
            if port.owner is entity and port.medium is not None:
                values[port.medium.iri] = port.medium
    for handle in handles:
        if handle.medium is not None:
            values[handle.medium.iri] = handle.medium
    for iri in roots:
        if iri in registry.enums_by_iri:
            values[iri] = registry.enums_by_iri[iri]
    if not values:
        root = registry.enums_by_iri.get(
            "http://data.ashrae.org/standard223#Substance-Medium"
        )
        if root is not None:
            values[root.iri] = root
    return sorted(values.values(), key=lambda value: value.iri)


def _make_points(
    entity: Entity, incident: dict[str, int], media: list[EnumValue]
) -> list[_Point]:
    registry = entity.meta.registry
    points: list[_Point] = []
    for cp in getattr(entity, "has_connection_point"):
        points.append(
            _Point(
                entity,
                type(cp),
                cp.name,
                z3.BoolVal(True),
                z3.Int(f"existing_{_safe(cp.name)}_medium"),
                cp,
            )
        )
    for port in entity.meta.model._port_intents:
        if port.owner is not entity:
            continue
        directions = (
            (port.direction,) if isinstance(port.direction, str) else port.direction
        )
        for direction_index, direction in enumerate(directions):
            cls_name = {
                "in": "InletConnectionPoint",
                "out": "OutletConnectionPoint",
                "bi": "BidirectionalConnectionPoint",
            }[direction]
            points.append(
                _Point(
                    entity,
                    registry.resolve(cls_name),
                    port.name,
                    z3.BoolVal(True)
                    if len(directions) == 1
                    else z3.Bool(
                        f"authored_{_safe(port.name)}_{direction_index}_active"
                    ),
                    z3.Int(f"authored_{_safe(port.name)}_medium"),
                    authored=port,
                )
            )
    slots = _all_slots(type(entity)) + _constraint_slots(type(entity))
    classes: dict[type[Entity], int] = {}
    # Slots of one class add up: an inlet for water and another for
    # electricity need two inlets. A slot whose maximum is 0 forbids points.
    for slot in slots:
        if slot.max_count == 0:
            continue
        cls = registry.resolve(slot.cp_class)
        classes[cls] = classes.get(cls, 0) + max(slot.min_count, slot.max_count or 0)
    for cls in classes:
        direction = _direction_of(cls)
        for side in ("in", "out"):
            if direction in {side, "bi"}:
                classes[cls] = max(classes[cls], incident[side])
    # Shape slots are lower bounds, not a closed list: SHACL leaves other
    # connection points open, so a direction no slot covers gets generic
    # points. Shape maximums still bound the total.
    covered = {_direction_of(cls) for cls in classes}
    for direction in ("in", "out"):
        if incident[direction] and not covered & {direction, "bi"}:
            name = (
                "InletConnectionPoint" if direction == "in" else "OutletConnectionPoint"
            )
            classes[registry.resolve(name)] = incident[direction]
    existing_names = {point.name for point in points}
    for cls, count in sorted(classes.items(), key=lambda item: item[0].__name__):
        existing_count = sum(
            point.existing is not None and point.existing.meta.is_a(cls)
            for point in points
        )
        count = max(count - existing_count, 0)
        direction = _direction_of(cls)
        for offset in range(count):
            base = f"{entity.name}-{direction}"
            name = base if offset == 0 else f"{base}_{offset + 1}"
            while name in existing_names:
                offset += 1
                name = f"{base}_{offset + 1}"
            existing_names.add(name)
            points.append(
                _Point(
                    entity,
                    cls,
                    name,
                    z3.Bool(
                        f"point_{_safe(entity.name)}_{_safe(cls.__name__)}_{offset}"
                    ),
                    z3.Int(
                        f"point_{_safe(entity.name)}_{_safe(cls.__name__)}_{offset}_medium"
                    ),
                )
            )
    return points


def _slot_expr(
    points: list[_Point],
    slot: CPSlot,
    media: list[EnumValue],
    enum_ids: dict[str, int],
) -> z3.BoolRef:
    slot_cls = points[0].owner.meta.registry.resolve(slot.cp_class)
    matching = [
        z3.And(point.active, _medium_allowed(point.medium, slot, media, enum_ids))
        for point in points
        if point.cls.meta.is_a(slot_cls)
        and (
            slot.label is None
            or point.authored is not None
            and point.authored.label == slot.label
            or point.existing is not None
            and point.existing.label == slot.label
        )
    ]
    count = (
        z3.Sum([z3.If(item, 1, 0) for item in matching]) if matching else z3.IntVal(0)
    )
    terms = [count >= slot.min_count]
    if slot.max_count is not None:
        terms.append(count <= slot.max_count)
    return z3.And(terms)


def _constraint_expr(
    points: list[_Point],
    constraint: CPConstraint,
    media: list[EnumValue],
    enum_ids: dict[str, int],
) -> z3.BoolRef:
    if constraint.operator == "slot":
        assert constraint.slot is not None
        return _slot_expr(points, constraint.slot, media, enum_ids)
    children = [
        _constraint_expr(points, child, media, enum_ids)
        for child in constraint.children
    ]
    if constraint.operator == "and":
        return z3.And(children)
    if constraint.operator == "or":
        return z3.Or(children)
    if constraint.operator == "xone":
        return z3.PbEq([(child, 1) for child in children], 1)
    raise ValueError("validation-only connection constraints cannot be solved")


def _medium_allowed(
    variable: z3.ArithRef,
    slot: CPSlot,
    media: list[EnumValue],
    enum_ids: dict[str, int],
) -> z3.BoolRef:
    roots = _slot_roots(slot)
    if not roots:
        return z3.BoolVal(True)
    allowed = [
        enum_ids[value.iri]
        for value in media
        if any(value.is_a(root) for root in roots)
    ]
    return z3.Or([variable == value for value in allowed])


def _eligible(
    points: list[_Point], endpoint: Entity | PortHandle | PointGroupRef, direction: str
) -> list[_Point]:
    from .core.points import PointGroupRef

    names = {
        "out": {"OutletConnectionPoint", "BidirectionalConnectionPoint"},
        "in": {"InletConnectionPoint", "BidirectionalConnectionPoint"},
    }[direction]
    return [
        point
        for point in points
        if point.owner is _owner(endpoint)
        and (
            not isinstance(endpoint, PointGroupRef)
            or point.authored in {reference._port for reference in endpoint.points}
        )
        and (not isinstance(endpoint, PortHandle) or point.authored is endpoint)
        and (
            isinstance(endpoint, (PortHandle, PointGroupRef))
            or getattr(endpoint, "owner", None) is None
            or point.existing is endpoint
        )
        and any(base.__name__ in names for base in point.cls.__mro__)
    ]


def _medium_affinity_penalty(
    entities: set[Entity],
    points: list[_Point],
    media: list[EnumValue],
    enum_ids: dict[str, int],
) -> z3.ArithRef:
    """Penalty for differing media on ports with overlapping permissions.

    This is a preference, not a physical preservation rule. Hard constraints
    come from SHACL domains and connection endpoints; the objective ranks
    otherwise-valid assignments by how coherently they use the media that an
    equipment/entity kind permits.
    """
    penalties: list[z3.ArithRef] = []
    for entity in entities:
        owned = [point for point in points if point.owner is entity]
        for index, left in enumerate(owned):
            for right in owned[index + 1 :]:
                if not (
                    _possible_medium_ids(left, media, enum_ids)
                    & _possible_medium_ids(right, media, enum_ids)
                ):
                    continue
                penalties.append(
                    z3.If(
                        z3.And(
                            left.active,
                            right.active,
                            left.medium != right.medium,
                        ),
                        1,
                        0,
                    )
                )
    return z3.Sum(penalties) if penalties else z3.IntVal(0)


def _point_roots(point: _Point) -> set[str]:
    registry = point.owner.meta.registry
    return {
        root
        for slot in _all_slots(type(point.owner)) + _constraint_slots(type(point.owner))
        if point.cls.meta.is_a(registry.resolve(slot.cp_class))
        for root in _slot_roots(slot)
    }


def _stated_medium(point: _Point) -> EnumValue | None:
    """The medium the user gave this port or concrete point, if any."""
    if point.authored is not None:
        return point.authored.medium
    if point.existing is not None:
        return getattr(point.existing, "medium")
    return None


def _possible_medium_ids(
    point: _Point,
    media: list[EnumValue],
    enum_ids: dict[str, int],
) -> set[int]:
    stated = _stated_medium(point)
    if stated is not None and stated.iri in enum_ids:
        return {enum_ids[stated.iri]}
    roots = _point_roots(point)
    if not roots:
        return set(enum_ids.values())
    return {
        enum_ids[value.iri]
        for value in media
        if any(value.is_a(root) for root in roots)
    }


def _medium_in_roots(
    variable: z3.ArithRef,
    roots: Iterable[str],
    media: list[EnumValue],
    enum_ids: dict[str, int],
) -> z3.BoolRef:
    allowed = [
        enum_ids[value.iri]
        for value in media
        if any(value.is_a(root) for root in roots)
    ]
    return z3.Or([variable == value for value in allowed])


def _minimize_active(solver: z3.Solver, points: list[_Point]) -> None:
    candidates = [point.active for point in points if point.existing is None]
    if not candidates:
        return
    total = z3.Sum([z3.If(active, 1, 0) for active in candidates])
    _minimize_expression(solver, total)


def _minimize_expression(solver: z3.Solver, expression: z3.ArithRef) -> None:
    """Constrain an integer objective to its minimum using the core solver."""
    while solver.check() == z3.sat:
        evaluated = z3.simplify(solver.model().eval(expression, model_completion=True))
        value = evaluated.as_long()
        solver.push()
        solver.add(expression < value)
        if solver.check() == z3.unsat:
            solver.pop()
            solver.add(expression == value)
            return
        solver.pop()
        solver.add(expression < value)


def _observable_expressions(
    entities: set[Entity],
    points: list[_Point],
    handles: list[ConnectionHandle],
    selections: dict[tuple[int, int], z3.BoolRef],
    intent_mediums: dict[int, z3.ArithRef],
) -> list[z3.ArithRef]:
    expressions: list[z3.ArithRef] = list(intent_mediums.values())
    for point in points:
        if point.authored is not None:
            expressions.append(z3.If(point.active, point.medium, -1))
    for entity in sorted(entities, key=lambda item: item.name):
        classes = sorted(
            {point.cls for point in points if point.owner is entity},
            key=lambda cls: cls.__name__,
        )
        for cls in classes:
            expressions.append(
                z3.Sum(
                    [
                        z3.If(point.active, 1, 0)
                        for point in points
                        if point.owner is entity and point.cls is cls
                    ]
                )
            )
    for handle in handles:
        for side_endpoint in (handle.source, handle.target):
            side_owner = _owner(side_endpoint)
            groups: dict[tuple[str, str], list[int]] = {}
            for index, point in enumerate(points):
                if point.owner is not side_owner:
                    continue
                key = _selection_group(point)
                groups.setdefault(key, []).append(index)
            for indexes in groups.values():
                expressions.append(
                    z3.Sum(
                        [
                            z3.If(
                                selections.get(
                                    (handle.identifier, index), z3.BoolVal(False)
                                ),
                                1,
                                0,
                            )
                            for index in indexes
                        ]
                    )
                )
    return expressions


def _selection_group(point: _Point) -> tuple[str, str]:
    """Group truly interchangeable points while preserving named choices."""
    if point.authored is not None:
        key = point.authored.symmetry_key or point.authored.name
        return ("authored", key)
    if point.existing is not None:
        existing = point.existing
        if getattr(existing, "_from_shape", False) and (
            getattr(existing, "connection") is None
        ):
            medium = getattr(existing, "medium")
            label = existing.label if existing.label != existing.name else ""
            return ("shape", f"{type(existing).__name__} {medium.iri} {label}")
        return ("existing", existing.name)
    return ("generated", point.cls.__name__)


def _extract_plan(
    handles: list[ConnectionHandle],
    points: list[_Point],
    selections: dict[tuple[int, int], z3.BoolRef],
    intent_mediums: dict[int, z3.ArithRef],
    model: z3.ModelRef,
    by_id: dict[int, EnumValue],
    connector: S223Connector,
) -> _Plan:
    results: dict[int, _PointResult] = {}
    materialized: list[_PointResult] = []
    for index, point in enumerate(points):
        if z3.is_true(model.eval(point.active, model_completion=True)):
            result = _PointResult(
                point.owner,
                point.cls,
                point.name,
                by_id[model.eval(point.medium, model_completion=True).as_long()],
                point.existing,
                point.authored,
            )
            results[index] = result
            materialized.append(result)
    intent_results: list[_IntentResult] = []
    for handle in handles:
        selected = [
            index
            for index in results
            if z3.is_true(
                model.eval(
                    selections.get((handle.identifier, index), z3.BoolVal(False)),
                    model_completion=True,
                )
            )
        ]
        source_owner = _owner(handle.source)
        target_owner = _owner(handle.target)
        source_index = next(
            index for index in selected if points[index].owner is source_owner
        )
        target_index = next(
            index for index in selected if points[index].owner is target_owner
        )
        medium = by_id[
            model.eval(
                intent_mediums[handle.identifier], model_completion=True
            ).as_long()
        ]
        connection_class = handle.connection_class or _connection_class(
            connector, medium
        )
        intent_results.append(
            _IntentResult(
                handle,
                results[source_index],
                results[target_index],
                medium,
                connection_class,
            )
        )
    return _Plan(tuple(materialized), tuple(intent_results))


def _connection_class(connector: S223Connector, medium: EnumValue) -> type[Entity]:
    node: EnumValue | None = medium
    while node is not None:
        name = connector.connection_classes.get(node.iri)
        if name is not None:
            return connector.registry.resolve(name)
        node = node.parent
    return connector.registry.resolve("Connection")


def _materialize(model: Model, plans: list[_Plan]) -> ResolvedModel:
    build = Snapshot(model)
    snapshot, mapping = build.model, build.entities
    point_entities: dict[tuple[int, str], Entity] = {}
    connection_entities = build.connections
    explanations = build.explanations
    authored_points: dict[PortHandle, Entity] = {}
    for plan in plans:
        for point in plan.points:
            key = (id(point.owner), point.name)
            if point.existing is not None:
                point_entities[key] = mapping[point.existing]
                continue
            owner = mapping[point.owner]
            point_entities[key] = point.cls(
                point.name,
                medium=point.medium,
                owner=owner,
                label=(
                    point.authored.label
                    if point.authored and point.authored.label
                    else None
                ),
                model=snapshot,
            )
            if point.authored is not None:
                authored_points[point.authored] = point_entities[key]
        for intent in plan.intents:
            source = point_entities[(id(intent.source.owner), intent.source.name)]
            target = point_entities[(id(intent.target.owner), intent.target.name)]
            connection = intent.connection_class(
                intent.handle.name,
                connects_at=[source, target],
                medium=intent.medium,
                label=intent.handle.label,
                comment=intent.handle.comment,
                model=snapshot,
            )
            for name, value in intent.handle._assignments.items():
                setattr(connection, name, build.copy(value))
            connection_entities[intent.handle.identifier] = connection
            explanations[intent.handle.identifier] = _explain_intent(intent)
    for handle, point in authored_points.items():
        if handle.roles:
            setattr(point, "has_role", handle.roles)
        for prop in handle._properties:
            getattr(point, "has_property").add(mapping[prop])
        for authored_system in handle._boundary_systems:
            system = mapping[authored_system]
            getattr(system, "has_boundary_connection_point").add(point)
        if handle.paired_with is not None and handle.paired_with in authored_points:
            setattr(
                point,
                "paired_with",
                authored_points[handle.paired_with],
            )
        target = handle.maps_to
        if isinstance(target, PortHandle):
            setattr(point, "maps_to", authored_points[target])
        elif target is not None:
            setattr(point, "maps_to", mapping[target])
    for authored_system, authored_members in model._system_intents:
        system = mapping[authored_system]
        members = set(authored_members)
        for plan in plans:
            for intent in plan.intents:
                source_inside = intent.source.owner in members
                target_inside = intent.target.owner in members
                if source_inside == target_inside:
                    continue
                boundary = intent.source if source_inside else intent.target
                point = point_entities[(id(boundary.owner), boundary.name)]
                getattr(system, "has_boundary_connection_point").add(point)
    _place_deferred_links(snapshot, authored_points, connection_entities)
    _fill_property_media(snapshot)
    return build.finish()


def _explain_intent(intent: _IntentResult) -> ResolutionExplanation:
    """Classify the strongest authored or inferred source of a medium."""
    handle = intent.handle
    evidence = [
        f"selected {intent.source.cls.__name__} {intent.source.name}",
        f"selected {intent.target.cls.__name__} {intent.target.name}",
    ]
    if handle.medium is not None:
        reason = "explicit connection"
        evidence.append(f"{handle.name}.medium = {_local(handle.medium.iri)}")
    else:
        explicit = _point_medium_evidence(intent.source) or _point_medium_evidence(
            intent.target
        )
        paired = _paired_medium_evidence(intent.source) or _paired_medium_evidence(
            intent.target
        )
        if explicit is not None:
            reason = "explicit port"
            evidence.append(explicit)
        elif paired is not None:
            reason = "paired port"
            evidence.append(paired)
        elif _ontology_determines_medium(intent):
            reason = "ontology constraint"
            evidence.append("connection-point SHACL domains admit one medium")
        else:
            reason = "affinity preference"
            evidence.append(
                "the solver minimized medium changes among otherwise valid choices"
            )
    return ResolutionExplanation(
        connection=handle.name,
        medium=intent.medium,
        source_point=intent.source.name,
        target_point=intent.target.name,
        medium_reason=reason,
        evidence=tuple(evidence),
    )


def _point_medium_evidence(point: _PointResult) -> str | None:
    if point.authored is not None and point.authored.medium is not None:
        return f"{point.authored.name}.medium = {_local(point.authored.medium.iri)}"
    if point.existing is not None:
        medium = getattr(point.existing, "medium", None)
        if medium is not None:
            return f"{point.existing.name}.medium = {_local(medium.iri)}"
    return None


def _paired_medium_evidence(point: _PointResult) -> str | None:
    if point.authored is not None and point.authored.paired_with is not None:
        paired = point.authored.paired_with
        if paired.medium is not None:
            return (
                f"{point.authored.name} is paired with {paired.name}, "
                f"whose medium is {_local(paired.medium.iri)}"
            )
    if point.existing is not None:
        paired = getattr(point.existing, "paired_with", None)
        medium = getattr(paired, "medium", None) if paired is not None else None
        if medium is not None:
            assert paired is not None
            return (
                f"{point.existing.name} is paired with {paired.name}, "
                f"whose medium is {_local(medium.iri)}"
            )
    return None


def _ontology_determines_medium(intent: _IntentResult) -> bool:
    source_roots = _result_roots(intent.source)
    target_roots = _result_roots(intent.target)
    roots = source_roots | target_roots
    if not roots:
        return False
    registry = intent.source.owner.meta.registry
    allowed = {
        value.iri
        for value in registry.enums_by_iri.values()
        if any(value.is_a(root) for root in roots)
    }
    return allowed == {intent.medium.iri}


def _result_roots(point: _PointResult) -> set[str]:
    registry = point.owner.meta.registry
    return {
        root
        for slot in _all_slots(type(point.owner)) + _constraint_slots(type(point.owner))
        if point.cls.meta.is_a(registry.resolve(slot.cp_class))
        for root in _slot_roots(slot)
    }


def _owner(endpoint: Entity | PortHandle | PointGroupRef) -> Entity:
    from .core.points import endpoint_owner

    return endpoint_owner(endpoint)


def _place_deferred_links(
    snapshot: Model,
    points: dict[PortHandle, Entity],
    connections: dict[int, Entity],
) -> None:
    """Replace ports and connection handles in links with concrete entities."""

    def concrete(entity: Entity, name: str, value: Any) -> Any:
        if isinstance(value, PortHandle):
            if value not in points:
                raise ModelingError(
                    f"{entity.name}.{name}: port {value.name!r} was not resolved"
                )
            return points[value]
        if isinstance(value, ConnectionHandle):
            if value.identifier not in connections:
                raise ModelingError(
                    f"{entity.name}.{name}: connection {value.name!r} was not resolved"
                )
            return connections[value.identifier]
        return value

    for entity in snapshot.entities:
        for name, value in entity._data.items():
            entity._data[name] = concrete(entity, name, value)
        for name, store in entity._rels.items():
            store._items = [concrete(entity, name, item) for item in store._items]


def _all_slots(cls: type[Entity]) -> list[CPSlot]:
    return [
        slot
        for base in cls.__mro__
        if (info := base.__dict__.get("_classinfo")) is not None
        for slot in info.cp_slots
    ]


def _all_constraints(cls: type[Entity]) -> list[CPConstraint]:
    return [
        constraint
        for base in cls.__mro__
        if (info := base.__dict__.get("_classinfo")) is not None
        for constraint in info.cp_constraints
    ]


def _constraint_slots(cls: type[Entity]) -> list[CPSlot]:
    slots: list[CPSlot] = []

    def visit(constraint: CPConstraint) -> None:
        if constraint.slot is not None:
            slots.append(constraint.slot)
        for child in constraint.children:
            visit(child)

    for constraint in _all_constraints(cls):
        if not _contains_opaque(constraint):
            visit(constraint)
    return slots


def _contains_opaque(constraint: CPConstraint) -> bool:
    return constraint.operator == "opaque" or any(
        _contains_opaque(child) for child in constraint.children
    )


def _slot_roots(slot: CPSlot) -> tuple[str, ...]:
    if slot.medium_options:
        return slot.medium_options
    return (slot.medium,) if slot.medium is not None else ()


def _direction_of(cls: type[Entity]) -> str:
    namespace = "http://data.ashrae.org/standard223#"
    directions = {
        direction
        for name, direction in (
            ("BidirectionalConnectionPoint", "bi"),
            ("InletConnectionPoint", "in"),
            ("OutletConnectionPoint", "out"),
        )
        if cls.meta.is_a(namespace + name)
    }
    if len(directions) != 1:
        raise ModelingError(f"{cls.meta.iri}: missing or ambiguous point direction")
    return directions.pop()


def _safe(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value)
