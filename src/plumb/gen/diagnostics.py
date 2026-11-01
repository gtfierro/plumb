"""Source-linked compiler support reports shared by both front ends.

Reports describe the generated projections as well as the authoritative SHACL
constraints. A Python datatype or class-range projection does not claim to
replace full RDF validation.
"""

from __future__ import annotations

from collections.abc import Iterable
import hashlib
import json
from typing import Any

from rdflib import BNode, Graph, RDF, URIRef
from rdflib.namespace import SH
from rdflib.term import Node
from rdflib.compare import to_canonical_graph

from .constraints import DATATYPES
from .ir import ClassIR, PropIR
from .stable import source_id

FILENAME = "_support.json"
FORMAT = 2


class CompilationError(ValueError):
    """A compilation failure with machine-readable diagnostic records."""

    def __init__(self, diagnostics: Iterable[dict[str, Any]]) -> None:
        self.diagnostics = tuple(diagnostics)
        super().__init__(
            "\n".join(
                f"{record['kind']} binding {record['target']}: {record['reason']}"
                for record in self.diagnostics
            )
        )


_ANNOTATIONS = {
    SH.path,
    SH.targetClass,
    SH.targetNode,
    SH.targetSubjectsOf,
    SH.targetObjectsOf,
    SH.name,
    SH.description,
    SH.message,
    SH.severity,
    SH.order,
    SH.group,
    SH.declare,
    SH.prefixes,
    SH.prefix,
    SH.namespace,
}
_S223 = "http://data.ashrae.org/standard223#"
_BOOLEAN_LISTS = {SH["and"], SH["or"], SH.xone}
_SHAPE_REFERENCES = {
    SH.property,
    SH.node,
    SH.sparql,
    SH.qualifiedValueShape,
    SH["not"],
    SH.prefixes,
    SH.declare,
}


def support_report(
    graph: Graph,
    classes: Iterable[ClassIR],
    *,
    bindings: Iterable[dict[str, Any]] = (),
    connections: Iterable[dict[str, object]] = (),
    quantities: Iterable[dict[str, Any]] = (),
    profiles: Iterable[ClassIR] = (),
) -> str:
    """Inventory source constraints and the checks generated from them."""
    # This inventory records enforcement, not just recognized syntax. A source
    # can be present in the IR yet remain validation-only (an unknown boolean
    # branch or an imported-class profile, for example). Only advertise runtime
    # or solver support when the corresponding projection actually owns it.
    records: list[dict[str, Any]] = []
    seen = set()
    profiles = list(profiles)
    profile_targets = {symbol.iri for symbol in profiles}

    def source_groups(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: source_id(BNode(item))
                if key == "source" and isinstance(item, str)
                else source_groups(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [source_groups(item) for item in value]
        return value

    connections = [source_groups(item) for item in connections]
    quantities = list(quantities)
    bindings = list(bindings)
    value_keys: dict[tuple[Node, Node], str] = {}
    direct_slots = {
        (item["target"], item["source"]): item for item in connections if "path" in item
    }

    def walk(
        target: str,
        shape: Node,
        props: dict[str, PropIR],
        *,
        path: Node | None = None,
        owner: Node | None = None,
        quantity: dict[str, Any] | None = None,
    ) -> None:
        # A shared source shape can apply to different targets or property
        # paths. Those are separate checks even if their RDF node is identical;
        # deduplicating solely by shape would hide part of the support inventory.
        key = (target, shape, path, owner)
        if key in seen:
            return
        seen.add(key)
        if graph.value(shape, SH.path) is not None:
            path, owner = graph.value(shape, SH.path), shape
        prop = props.get(str(path)) if path is not None else None
        projected = prop is not None and str(owner) in prop.sources
        for parameter, value in sorted(
            graph.predicate_objects(shape),
            key=lambda pair: (str(pair[0]), pair[1].n3()),
        ):
            if not str(parameter).startswith(str(SH)) or parameter in _ANNOTATIONS:
                continue
            if parameter == SH.property:
                walk(target, value, props, quantity=quantity)
                continue
            enforcement = ["validation"]
            reason = "Outside this generated projection; retained for SHACL validation."
            if projected and prop is not None:
                if parameter == SH.minCount and prop.required:
                    enforcement = ["constructor", "validation"]
                    reason = "Minimum checked at constructor completion and graph validation."
                elif parameter == SH.maxCount:
                    enforcement = ["runtime", "validation"]
                    reason = "Effective upper bound checked before mutation."
                elif parameter == SH["class"] and any(
                    str(value) in group for group in prop.range_groups
                ):
                    enforcement = ["runtime", "validation"]
                    reason = "Semantic class-range projection."
                elif (
                    parameter == SH.datatype
                    and isinstance(value, URIRef)
                    and value in DATATYPES
                ):
                    enforcement = ["runtime", "validation"]
                    reason = "Python type projection; exact RDF datatype remains a validation check."
                elif parameter == SH.hasValue and value in prop.required_values:
                    enforcement = ["constructor", "runtime", "validation"]
                    reason = "Required member inserted and protected against mutation."
                elif parameter == SH.defaultValue and value in prop.default_values:
                    enforcement = ["constructor"]
                    reason = (
                        "Replaceable authoring default; no graph validity requirement."
                    )
                elif parameter == SH["in"] and prop.choices is not None:
                    enforcement = ["runtime", "validation"]
                    reason = "Finite choices intersected with inherited choices."
                elif parameter == SH["or"] and prop.range_groups:
                    enforcement = ["runtime", "validation"]
                    reason = "Necessary class-range projection; the full boolean constraint remains in validation."
                elif parameter == SH.minCount:
                    reason = "Minimum retained for graph validation to permit staged authoring."
            if parameter in {SH.node, SH["and"]}:
                reason = "Conjunctive property projections are listed separately below this source shape."
            slot = (
                direct_slots.get((target, source_id(owner)))
                if owner is not None
                else None
            )
            if slot is not None and parameter in {
                SH.qualifiedMinCount,
                SH.qualifiedMaxCount,
                SH.qualifiedValueShape,
            }:
                if slot["support"] == "solver":
                    enforcement = ["solver", "validation"]
                    reason = "S223 connection projection; see connections for expression and assertion scope."
                else:
                    reason = str(slot.get("reason") or reason)
            if quantity is not None:
                local = str(path)
                if local == _S223 + "hasValue" and parameter in {
                    SH.minInclusive,
                    SH.maxInclusive,
                    SH["in"],
                    SH.hasValue,
                    SH.defaultValue,
                    SH.datatype,
                    SH.minCount,
                    SH.maxCount,
                }:
                    enforcement = ["constructor", "runtime", "validation"]
                    reason = "Scalar quantity projection; see quantities for numeric checks and defaults."
                elif local in {
                    "http://qudt.org/schema/qudt/hasUnit",
                    "http://qudt.org/schema/qudt/hasQuantityKind",
                } and parameter in {SH.hasValue, SH.defaultValue, SH["in"]}:
                    enforcement = ["constructor", "runtime", "validation"]
                    reason = "Quantity kind/unit projection; see quantities for fixed and replaceable values."
            if target in profile_targets:
                enforcement = ["validation"]
                reason = "Model-scoped profile constraint on a canonical imported class; checked by SHACL validation."
            records.append(
                {
                    "target": target,
                    "source": source_id(shape),
                    "path": str(path) if path is not None else None,
                    "parameter": str(parameter),
                    "value": f"_:{source_id(value)}"
                    if isinstance(value, BNode)
                    else value.n3(),
                    "value_key": _value_key(graph, parameter, value, value_keys),
                    "enforcement": enforcement,
                    "reason": reason,
                    **({"profile": True} if target in profile_targets else {}),
                }
            )
            if parameter == SH.node:
                walk(target, value, props, path=path, owner=owner, quantity=quantity)
            elif parameter == SH["and"]:
                for node in graph.items(value):
                    walk(target, node, props, path=path, owner=owner, quantity=quantity)
            # Disjunctions and qualified branches are reported as expressions,
            # never as independently enforced conjuncts.

    for symbol in sorted([*classes, *profiles], key=lambda item: item.iri):
        props = (
            {}
            if symbol.iri in profile_targets
            else {prop.predicate: prop for prop in symbol.effective_props.values()}
        )
        for root in [
            URIRef(symbol.iri),
            *sorted(graph.subjects(SH.targetClass, URIRef(symbol.iri)), key=str),
        ]:
            walk(symbol.iri, root, props)
    for field in quantities:
        walk(field["shape"], URIRef(field["shape"]), {}, quantity=field)
    return (
        json.dumps(
            {
                "format": FORMAT,
                "summary": {
                    **{
                        stage: sum(stage in record["enforcement"] for record in records)
                        for stage in ("constructor", "runtime", "solver")
                    },
                    "validation_only": sum(
                        record["enforcement"] == ["validation"] for record in records
                    ),
                    "optional_bindings_missing": sum(
                        not record["required"] and record["status"] == "missing"
                        for record in bindings
                    ),
                },
                "constraints": sorted(
                    records, key=lambda item: json.dumps(item, sort_keys=True)
                ),
                "bindings": bindings,
                "profile_targets": sorted(profile_targets),
                "connections": connections,
                "quantities": quantities,
            },
            indent=2,
            sort_keys=True,
            default=lambda value: value.n3(),
        )
        + "\n"
    )


def _value_key(
    graph: Graph, parameter: Node, value: Node, cache: dict[tuple[Node, Node], str]
) -> str:
    """Fingerprint a constraint value independently of anonymous source context.

    Follow blank-node contents and explicit shape/query/prefix references, not
    class ranges or vocabulary values. This is an RDF
    identity check, not a proof of equivalence between arbitrary SHACL programs.
    """
    if (parameter, value) in cache:
        return cache[parameter, value]
    if parameter in {SH["in"], SH["and"], SH["or"], SH.xone} and (
        value == RDF.nil or (value, RDF.first, None) in graph
    ):
        members = [
            _value_key(
                graph,
                SH.node if parameter in _BOOLEAN_LISTS else SH.hasValue,
                member,
                cache,
            )
            for member in graph.items(value)
        ]
        # All four operators are order-independent. Repeated xone alternatives
        # remain significant because xone counts successful branches.
        key = json.dumps(sorted(members if parameter == SH.xone else set(members)))
    elif not isinstance(value, BNode) and parameter not in {
        SH.sparql,
        SH.node,
        SH.qualifiedValueShape,
        SH["not"],
    }:
        key = value.n3()
    else:
        # Diagnostic source labels include incoming context for location. A
        # review fingerprint must exclude that context: moving an unchanged
        # expression beneath another wrapper must not change its value identity.
        # Anchor the rooted subgraph and canonicalize it independently, following
        # explicit shape references but not arbitrary class/vocabulary graphs.
        rooted = Graph()
        rooted.add((URIRef("urn:plumb:review:root"), RDF_VALUE, value))
        pending, seen = [(value, parameter)], set()
        while pending:
            node, context = pending.pop()
            if (node, context) in seen:
                continue
            seen.add((node, context))
            for predicate, child in graph.predicate_objects(node):
                # Prefix carriers are often owl:Ontology nodes. Their version,
                # imports, and documentation are not part of a query's meaning.
                if context == SH.prefixes and predicate != SH.declare:
                    continue
                rooted.add((node, predicate, child))
                if (
                    isinstance(child, BNode)
                    or predicate in _SHAPE_REFERENCES
                    or context in _BOOLEAN_LISTS
                    and predicate == RDF.first
                ):
                    pending.append(
                        (
                            child,
                            context
                            if context in _BOOLEAN_LISTS and predicate == RDF.rest
                            else predicate,
                        )
                    )
        content = "\n".join(
            sorted(to_canonical_graph(rooted).serialize(format="nt").splitlines())
        )
        key = "sha256:" + hashlib.sha256(content.encode()).hexdigest()
    cache[parameter, value] = key
    return key


RDF_VALUE = URIRef("urn:plumb:review:value")
