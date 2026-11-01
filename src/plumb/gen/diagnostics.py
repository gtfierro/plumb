"""Source-linked compiler support reports shared by both front ends.

Reports describe the generated projections as well as the authoritative SHACL
constraints. A Python datatype or class-range projection does not claim to
replace full RDF validation.
"""

from __future__ import annotations

from collections.abc import Iterable
import json
from typing import Any

from rdflib import BNode, Graph, URIRef
from rdflib.namespace import SH
from rdflib.term import Node

from .constraints import DATATYPES
from .ir import ClassIR, PropIR
from .stable import source_id

FILENAME = "_support.json"


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
                "format": 1,
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
