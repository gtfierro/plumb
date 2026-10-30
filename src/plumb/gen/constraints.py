"""Normalize the supported conjunctive SHACL subset for both compiler fronts.

Ranges are conjunctions of alternative groups: ``((A, B), (C,))`` means
``(A or B) and C``. Keeping those operators separate prevents inheritance
or repeated property shapes from turning restrictions into alternatives.
"""

from __future__ import annotations

from rdflib import Graph, URIRef
from rdflib.namespace import SH
from rdflib.term import Node


def property_shapes(
    graph: Graph,
    shape: Node,
    *,
    reject_disjunction: bool = False,
    active: frozenset[Node] = frozenset(),
) -> list[Node]:
    """Find properties reached through ``sh:node`` and ``sh:and`` conjunctions."""
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
