"""The compiler's S223 semantic adapter, also used for WaTr's S223 vocabulary.

IRI identity and RDF ancestry determine meaning. Python aliases and unrelated
terms with familiar local names never select connection semantics.
"""

from __future__ import annotations

from typing import Literal

from rdflib import Graph, Namespace, RDFS, URIRef
from rdflib.namespace import SH
from rdflib.term import Node

from .constraints import class_groups, property_shapes
from .ir import CPConstraintIR, CPSlotIR

NS = Namespace("http://data.ashrae.org/standard223#")
_DIRECTIONS: dict[URIRef, Literal["in", "out", "bi"]] = {
    NS.InletConnectionPoint: "in",
    NS.OutletConnectionPoint: "out",
    NS.BidirectionalConnectionPoint: "bi",
}


def direction(graph: Graph, value_class: URIRef) -> Literal["in", "out", "bi"] | None:
    """Resolve a direction through ontology ancestry, diagnosing ambiguity."""
    ancestry = set(graph.transitive_objects(value_class, RDFS.subClassOf))
    directions = {value for root, value in _DIRECTIONS.items() if root in ancestry}
    if len(directions) > 1:
        raise ValueError(f"{value_class}: ambiguous connection-point directions")
    return next(iter(directions)) if directions else None


def connection_slot(
    graph: Graph,
    shape: Node,
    qualified: Node,
    names: dict[str, str],
    enum_iris: set[str],
) -> tuple[CPSlotIR | None, str | None]:
    """Project one supported qualified hasConnectionPoint shape into a slot."""
    if graph.value(shape, SH.path) != NS.hasConnectionPoint:
        return (
            None,
            f"{graph.value(shape, SH.path)} is not the S223 equipment-point path",
        )
    classes = list(graph.objects(qualified, SH["class"]))
    value_class = classes[0] if len(classes) == 1 else None
    if not isinstance(value_class, URIRef) or str(value_class) not in names:
        return None, "qualified value class is not a single compiled class"
    flow = direction(graph, value_class)
    if flow is None:
        return None, f"{value_class} has no supported S223 point direction"
    groups: set[tuple[str, ...]] = set()
    for prop in property_shapes(graph, qualified):
        if graph.value(prop, SH.path) != NS.hasMedium:
            return (
                None,
                f"point qualifier on {graph.value(prop, SH.path)} is validation-only",
            )
        if graph.value(prop, SH.hasValue) is not None:
            return None, "exact-value medium qualifier is validation-only"
        groups.update(class_groups(graph, prop))
    if any(iri not in enum_iris for group in groups for iri in group):
        return None, "medium domain contains a class outside the compiled enumeration"
    media: set[str] = set()
    if groups:
        for iri in enum_iris:
            ancestors = {
                str(node)
                for node in graph.transitive_objects(URIRef(iri), RDFS.subClassOf)
            }
            if all(ancestors.intersection(group) for group in groups):
                media.add(iri)
        if not media:
            raise ValueError(f"{shape}: incompatible connection medium constraints")
        # Retain the broadest roots of the intersection, not every descendant.
        media = {
            iri
            for iri in media
            if not any(
                str(parent) in media and str(parent) != iri
                for parent in graph.transitive_objects(URIRef(iri), RDFS.subClassOf)
            )
        }
    minimum = int(str(graph.value(shape, SH.qualifiedMinCount) or 0))
    value = graph.value(shape, SH.qualifiedMaxCount)
    maximum = int(str(value)) if value is not None else None
    if minimum < 0 or (maximum is not None and (maximum < 0 or minimum > maximum)):
        raise ValueError(f"{shape}: contradictory qualified cardinalities")
    return CPSlotIR(
        cp_class=names[str(value_class)],
        direction=flow,
        medium=next(iter(media)) if len(media) == 1 else None,
        medium_options=tuple(sorted(media)) if len(media) > 1 else (),
        min_count=minimum,
        max_count=maximum,
    ), None


def connection_expression(
    graph: Graph,
    shape: Node,
    names: dict[str, str],
    enum_iris: set[str],
    active: set[Node],
) -> CPConstraintIR:
    """Preserve boolean structure and validation-only branches conservatively."""
    if shape in active:
        return CPConstraintIR(
            operator="opaque",
            source=str(shape),
            reason="recursive or untranslated shape",
        )
    active = active | {shape}
    conjuncts: list[CPConstraintIR] = []
    for prop in graph.objects(shape, SH.property):
        qualified = graph.value(prop, SH.qualifiedValueShape)
        slot, reason = (
            connection_slot(graph, prop, qualified, names, enum_iris)
            if qualified is not None
            else (None, "untranslated property constraint")
        )
        conjuncts.append(
            CPConstraintIR(operator="slot", slot=slot)
            if slot is not None
            else CPConstraintIR(operator="opaque", source=str(prop), reason=reason)
        )
    for referenced in graph.objects(shape, SH.node):
        conjuncts.append(
            connection_expression(graph, referenced, names, enum_iris, active)
        )
    for operator in ("and", "or", "xone"):
        for members in graph.objects(shape, SH[operator]):
            conjuncts.append(
                CPConstraintIR(
                    operator=operator,
                    children=[
                        connection_expression(graph, member, names, enum_iris, active)
                        for member in graph.items(members)
                    ],
                )
            )
    known = {
        SH.property,
        SH.node,
        SH["and"],
        SH["or"],
        SH.xone,
        SH.name,
        SH.description,
        SH.order,
        SH.message,
        SH.severity,
        SH.group,
    }
    if any(
        str(predicate).startswith(str(SH)) and predicate not in known
        for predicate in graph.predicates(shape)
    ):
        conjuncts.append(
            CPConstraintIR(
                operator="opaque",
                source=str(shape),
                reason="untranslated SHACL constraints",
            )
        )
    if not conjuncts:
        return CPConstraintIR(
            operator="opaque",
            source=str(shape),
            reason="recursive or untranslated shape",
        )
    return (
        conjuncts[0]
        if len(conjuncts) == 1
        else CPConstraintIR(operator="and", children=conjuncts)
    )


def contains_opaque(expression: CPConstraintIR) -> bool:
    """Whether a projection depends on constraints outside the solver subset."""
    return expression.operator == "opaque" or any(
        contains_opaque(child) for child in expression.children
    )
