"""Normalize the supported conjunctive SHACL subset for both compiler fronts.

Ranges are conjunctions of alternative groups: ``((A, B), (C,))`` means
``(A or B) and C``. Keeping those operators separate prevents inheritance
or repeated property shapes from turning restrictions into alternatives.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Set
from dataclasses import replace

from rdflib import Graph, URIRef, XSD
from rdflib.namespace import SH
from rdflib.term import Node

from .ir import PropIR

DATATYPES: dict[URIRef, str] = {
    XSD.string: "str",
    XSD.normalizedString: "str",
    XSD.anyURI: "str",
    XSD.float: "float",
    XSD.double: "float",
    XSD.decimal: "float",
    XSD.integer: "int",
    XSD.int: "int",
    XSD.long: "int",
    XSD.nonNegativeInteger: "int",
    XSD.positiveInteger: "int",
    XSD.boolean: "bool",
}


def refine_property(prop: PropIR, graph: Graph, shapes: list[Node]) -> PropIR:
    """Intersect SHACL refinements with an effective inherited property."""
    result = replace(prop)
    result.min_count, result.max_count = cardinality(
        graph, shapes, minimum=prop.min_count, maximum=prop.max_count
    )
    result.required = prop.required or any(
        int(str(value)) > 0
        for shape in shapes
        for value in graph.objects(shape, SH.minCount)
    )
    result.sources = tuple(sorted(set(prop.sources) | {str(shape) for shape in shapes}))
    result.range_groups = tuple(
        sorted(
            set(prop.range_groups)
            | {group for shape in shapes for group in class_groups(graph, shape)}
        )
    )
    datatypes = {
        value for shape in shapes for value in graph.objects(shape, SH.datatype)
    }
    supported = {
        DATATYPES[value]
        for value in datatypes
        if isinstance(value, URIRef) and value in DATATYPES
    }
    if len(supported) > 1:
        raise ValueError(
            f"{prop.predicate}: incompatible datatypes; sources: {result.sources}"
        )
    if supported:
        datatype = supported.pop()
        if prop.kind == "literal" and prop.datatype != datatype:
            raise ValueError(f"{prop.predicate}: incompatible inherited datatype")
        result.kind, result.datatype = "literal", datatype
    result.required_values = _ordered(
        {
            *prop.required_values,
            *(value for shape in shapes for value in graph.objects(shape, SH.hasValue)),
        }
    )
    defaults = _ordered(
        {value for shape in shapes for value in graph.objects(shape, SH.defaultValue)}
    )
    result.default_values = defaults if defaults else prop.default_values
    choices = [set(prop.choices)] if prop.choices is not None else []
    choices.extend(
        set(graph.items(members))
        for shape in shapes
        for members in graph.objects(shape, SH["in"])
    )
    result.choices = _ordered(set.intersection(*choices)) if choices else None
    _check_values(result)
    return result


def merge_properties(left: PropIR, right: PropIR) -> PropIR:
    """Compose declarations by identity, preserving intersections and defaults."""
    if left.predicate != right.predicate:
        raise ValueError(
            f"property name collision {left.name}: {left.predicate}, {right.predicate}"
        )
    # Refinement is asymmetric only for authoring defaults/documentation: the
    # more local declaration wins there. Validity constraints remain conjunctive:
    # minima tighten upward, maxima downward, required members accumulate, and
    # choices intersect. None means unrestricted choices; () forbids all values.
    maxima = [n for n in (left.max_count, right.max_count) if n is not None]
    untyped = right.kind == "object" and not right.ranges and not right.range_groups
    choices = [set(prop.choices) for prop in (left, right) if prop.choices is not None]
    result = replace(
        right,
        kind=left.kind if untyped else right.kind,
        datatype=left.datatype if untyped else right.datatype,
        inverse=right.inverse or left.inverse,
        label=right.label or left.label,
        definition=right.definition or left.definition,
        required=left.required or right.required,
        min_count=max(left.min_count, right.min_count),
        max_count=min(maxima) if maxima else None,
        range_groups=tuple(sorted(set(left.range_groups) | set(right.range_groups))),
        sources=tuple(sorted(set(left.sources) | set(right.sources))),
        deferred=left.deferred or right.deferred,
        required_values=_ordered(
            set(left.required_values) | set(right.required_values)
        ),
        default_values=right.default_values or left.default_values,
        choices=_ordered(set.intersection(*choices)) if choices else None,
    )
    _check_values(result)
    return result


def project_ranges(
    prop: PropIR,
    names: Mapping[str, str],
    enum_iris: Set[str],
    is_a: Callable[[str, str], bool],
) -> PropIR:
    """Derive annotation ranges without weakening semantic intersections."""
    if not prop.range_groups:
        return prop
    candidates = {iri for group in prop.range_groups for iri in group}
    narrowed = {
        iri
        for iri in candidates
        if all(any(is_a(iri, root) for root in group) for group in prop.range_groups)
    }
    # Failure to find a named common subtype does not prove a contradiction:
    # RDF classes are not disjoint merely because the current closure lacks an
    # intersection class. Choose a conservative annotation and leave every
    # original conjunct in range_groups for runtime and SHACL enforcement.
    projection = narrowed or set(
        sorted(prop.range_groups, key=lambda group: (len(group), group))[0]
    )
    kind = "enum" if candidates <= enum_iris else prop.kind
    return replace(
        prop,
        kind=kind,
        ranges=tuple(sorted(names[iri] for iri in projection if iri in names)),
        enum_ranges=tuple(sorted(projection)) if kind == "enum" else (),
    )


def _ordered(values: Set[Node]) -> tuple[Node, ...]:
    return tuple(sorted(values, key=lambda value: value.n3()))


def _check_values(prop: PropIR) -> None:
    if (
        prop.max_count is not None
        and max(prop.min_count, len(prop.required_values)) > prop.max_count
    ):
        raise ValueError(
            f"{prop.predicate}: contradictory cardinalities; sources: {prop.sources}"
        )
    if prop.choices is not None and any(
        value not in prop.choices
        for value in (*prop.required_values, *prop.default_values)
    ):
        raise ValueError(
            f"{prop.predicate}: required/default value is outside sh:in; sources: {prop.sources}"
        )
    if (
        prop.max_count is not None
        and len(set(prop.default_values) | set(prop.required_values)) > prop.max_count
    ):
        raise ValueError(
            f"{prop.predicate}: defaults exceed cardinality; sources: {prop.sources}"
        )


def property_shapes(
    graph: Graph,
    shape: Node,
    *,
    reject_disjunction: bool = False,
    active: frozenset[Node] = frozenset(),
) -> list[Node]:
    """Find properties reached through ``sh:node`` and ``sh:and`` conjunctions."""
    # active is a recursion PATH, not a global visited set. A shared shape may
    # legitimately contribute to several owners or conjuncts; only revisiting
    # it while expanding itself is a recursive constructive definition.
    if shape in active:
        raise ValueError(f"{shape}: recursive constructive shape")
    active = active | {shape}
    result = list(graph.objects(shape, SH.property))
    nested = list(graph.objects(shape, SH.node))
    for members in graph.objects(shape, SH["and"]):
        nested.extend(graph.items(members))
    for node in nested:
        result.extend(
            property_shapes(
                graph, node, reject_disjunction=reject_disjunction, active=active
            )
        )
    if reject_disjunction and any(
        graph.value(shape, predicate) is not None for predicate in (SH["or"], SH.xone)
    ):
        raise ValueError(
            f"{shape}: disjunctive configuration needs explicit constructive selection"
        )
    return sorted(
        set(result),
        key=lambda node: (
            float(str(graph.value(node, SH.order) or 0)),
            str(graph.value(node, SH.name) or graph.value(node, SH.path) or node),
            str(node),
        ),
    )


def class_groups(
    graph: Graph, shape: Node, active: frozenset[Node] = frozenset()
) -> tuple[tuple[str, ...], ...]:
    """Extract class conjunctions and explicit class-only alternatives.

    Other forms stay in the bundled validation graph. In particular, an
    alternative with an unknown branch supplies no unconditional class range.
    """
    if shape in active:
        raise ValueError(f"{shape}: recursive class constraint")
    active = active | {shape}
    groups: list[tuple[str, ...]] = [
        (str(value),)
        for value in graph.objects(shape, SH["class"])
        if isinstance(value, URIRef)
    ]
    nested = list(graph.objects(shape, SH.node))
    for members in graph.objects(shape, SH["and"]):
        nested.extend(graph.items(members))
    for node in nested:
        groups.extend(class_groups(graph, node, active))
    for members in graph.objects(shape, SH["or"]):
        branches = [
            list(graph.objects(branch, SH["class"])) for branch in graph.items(members)
        ]
        if branches and all(
            len(branch) == 1 and isinstance(branch[0], URIRef) for branch in branches
        ):
            groups.append(tuple(sorted({str(branch[0]) for branch in branches})))
    return tuple(sorted(set(groups)))


def cardinality(
    graph: Graph,
    shapes: list[Node],
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> tuple[int, int | None]:
    """Intersect counts with an inherited bound, rejecting contradictions."""
    minima = [
        int(str(v)) for shape in shapes for v in graph.objects(shape, SH.minCount)
    ]
    maxima = [
        int(str(v)) for shape in shapes for v in graph.objects(shape, SH.maxCount)
    ]
    if any(value < 0 for value in [*minima, *maxima]):
        raise ValueError(f"{', '.join(map(str, shapes))}: negative cardinality")
    minimum = max([minimum, *minima])
    upper = [*maxima, *([maximum] if maximum is not None else [])]
    maximum = min(upper) if upper else None
    if maximum is not None and minimum > maximum:
        raise ValueError(
            f"{', '.join(map(str, shapes))}: contradictory cardinalities "
            f"({minimum}..{maximum})"
        )
    return minimum, maximum
