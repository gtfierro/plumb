"""Compare saved compiler output without importing packages or dependencies.

Effective symbols describe the Python/runtime contract; support records describe
checks that remain in validation. Source and build identity changes are reported
separately. This is a review aid, not an automatic compatibility verdict.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from rdflib.namespace import SH

from .diagnostics import FILENAME as SUPPORT_FILE, FORMAT as SUPPORT_FORMAT
from .ir import CPConstraintIR
from .symbols import FILENAME as SYMBOLS_FILE, Symbols


@dataclass(frozen=True)
class Change:
    kind: str
    category: str
    target: str
    path: str | None
    field: str
    before: Any
    after: Any


@dataclass(frozen=True)
class UpgradeReport:
    """Deterministic contract changes, separated from input/build provenance."""

    changes: tuple[Change, ...]
    provenance_changes: tuple[Change, ...]

    @property
    def changed(self) -> bool:
        return bool(self.changes or self.provenance_changes)

    def to_json(self) -> str:
        return (
            json.dumps({"format": 1, **asdict(self)}, indent=2, sort_keys=True) + "\n"
        )

    def render(self) -> str:
        lines = [
            f"{len(self.changes)} contract changes; "
            f"{len(self.provenance_changes)} provenance changes"
        ]
        for change in (*self.changes, *self.provenance_changes):
            target = change.target
            if change.path is not None:
                target += f" [{change.path}]"
            lines.append(
                f"{change.kind} {change.category} {target} {change.field}: "
                f"{_json(change.before)} -> {_json(change.after)}"
            )
        return "\n".join(lines) + "\n"


def compare_packages(before: str | Path, after: str | Path) -> UpgradeReport:
    """Review two generated package directories, with no Python execution.

    Both sides must be generated with a compiler that emits support format 2.
    Dependency exports need not be installed: their pinned digests are compared
    as provenance, and each changed dependency should also be reviewed directly.
    """
    old_facts, old_provenance = _read(Path(before))
    new_facts, new_provenance = _read(Path(after))
    return UpgradeReport(
        _diff(old_facts, new_facts), _diff(old_provenance, new_provenance)
    )


# A record is scoped by semantic identity, not a Python name or blank-node ID.
type _Key = tuple[str, str, str | None]
type _Facts = dict[_Key, dict[str, Any]]


def _read(directory: Path) -> tuple[_Facts, _Facts]:
    try:
        text = (directory / SYMBOLS_FILE).read_text()
        symbols = Symbols.decode(text, module="review", source=str(directory))
        export = json.loads(text)
        support = json.loads((directory / SUPPORT_FILE).read_text())
        if support["format"] != SUPPORT_FORMAT:
            raise ValueError(
                f"unsupported support report format {support['format']!r}; "
                "regenerate both versions with the same compiler"
            )
        facts: _Facts = {}
        for iri, symbol in symbols.classes.items():
            requirements = CPConstraintIR(
                "and",
                children=[
                    *(CPConstraintIR("slot", slot=slot) for slot in symbol.cp_slots),
                    *symbol.cp_constraints,
                ],
            )
            facts["class", iri, None] = {
                "public_name": symbol.name,
                "parents": sorted(symbol.parent_iris),
                "ancestors": sorted(symbol.ancestor_iris),
                "python_bases": list(symbol.parents),
                "abstract": symbol.abstract,
                "canonical": [symbol.canonical_module, symbol.canonical_name],
                "class_defaults": _set(symbol.class_defaults),
                "maximum_ports": symbol.maximum_ports,
                "named_points": _set(
                    {
                        key: value
                        for key, value in asdict(point).items()
                        if key != "source"
                    }
                    for point in symbol.points
                ),
                "port_requirements": _expression(requirements)
                if _has_slot(requirements)
                else None,
            }
            for prop in symbol.effective_props.values():
                projection = asdict(prop)
                for key in ("label", "definition", "sources"):
                    projection.pop(key)
                for key in ("required_values", "default_values", "choices"):
                    values = projection[key]
                    projection[key] = (
                        _set(value.n3() for value in values)
                        if values is not None
                        else None
                    )
                for key in ("ranges", "enum_ranges", "term_ranges"):
                    projection[key] = _set(projection[key])
                projection["range_groups"] = _set(
                    _set(group) for group in prop.range_groups
                )
                facts["property", iri, prop.predicate] = projection
        for iri, enum in symbols.enums.items():
            facts["enum", iri, None] = {
                "public_name": enum.name,
                "parent": enum.parent,
                "parents": _set(enum.parents),
                "constituents": _set(enum.constituents),
                "python_module": enum.python_module,
                "python_name": enum.python_name,
            }
        for iri, types in symbols.term_types.items():
            facts["term", iri, None] = {"types": sorted(types)}
        # node/and are conjunction wrappers; their independently reported leaves
        # carry the checks. Anonymous source IDs and explanatory prose are not
        # contract facts. value_key includes anonymous lists and executable text.
        for record in support["constraints"]:
            if record["parameter"] in {str(SH.node), str(SH["and"])}:
                continue
            key = ("support", record["target"], record["path"])
            parameter = record["parameter"]
            checks = facts.setdefault(key, {}).setdefault(parameter, [])
            checks.append(
                {
                    "value": record["value_key"],
                    "enforcement": sorted(record["enforcement"]),
                    "profile": record.get("profile", False),
                }
            )
        for key, fields in facts.items():
            if key[0] == "support":
                for parameter, checks in fields.items():
                    fields[parameter] = _set(checks)
        for binding in support["bindings"]:
            key = ("binding", _json(binding["target"]), binding["kind"])
            facts.setdefault(key, {}).setdefault("bindings", []).append(
                {
                    key: value
                    for key, value in binding.items()
                    if key not in {"target", "kind", "reason"}
                }
            )
        for key, fields in facts.items():
            if key[0] == "binding":
                fields["bindings"] = _set(fields["bindings"])
        for quantity in support["quantities"]:
            facts["quantity", quantity["shape"], None] = quantity
        provenance: _Facts = {
            ("ontology", symbols.ontology["iri"], None): symbols.ontology,
            ("source", "graph", None): {"sha256": export["graph_sha256"]},
        }
        for dependency in symbols.dependencies:
            provenance["dependency", dependency["module"], None] = dependency
        build_file = directory / "_build.json"
        if build_file.exists():
            build = json.loads(build_file.read_text())
            if build["format"] != 1:
                raise ValueError("unsupported build provenance format")
            provenance["compiler", "plumb", None] = build["compiler"]
            for name, source in build["sources"].items():
                provenance["source", name, None] = source
        return facts, provenance
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise ValueError(
            f"{directory}: cannot review generated package: {error}"
        ) from error


def _has_slot(expression: CPConstraintIR) -> bool:
    return expression.slot is not None or any(
        _has_slot(child) for child in expression.children
    )


def _expression(expression: CPConstraintIR) -> Any:
    if expression.operator == "slot":
        return {"slot": asdict(expression.slot)} if expression.slot else None
    if expression.operator == "opaque":
        return {"opaque": True}
    children = []
    for child in expression.children:
        normalized = _expression(child)
        if (
            expression.operator == "and"
            and isinstance(normalized, dict)
            and "and" in normalized
        ):
            children.extend(normalized["and"])
        else:
            children.append(normalized)
    # xone counts successful branches, so repeated branches are significant.
    values = (
        sorted(children, key=_json) if expression.operator == "xone" else _set(children)
    )
    if expression.operator == "and" and len(values) == 1:
        return values[0]
    return {expression.operator: values}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _set(values: Any) -> list[Any]:
    return [value for _, value in sorted({_json(v): v for v in values}.items())]


def _diff(before: _Facts, after: _Facts) -> tuple[Change, ...]:
    changes = []
    for key in sorted(before.keys() | after.keys(), key=_json):
        category, target, path = key
        if key not in before or key not in after:
            changes.append(
                Change(
                    "added" if key in after else "removed",
                    category,
                    target,
                    path,
                    "record",
                    before.get(key),
                    after.get(key),
                )
            )
            continue
        old, new = before[key], after[key]
        for field in sorted(old.keys() | new.keys()):
            if old.get(field) != new.get(field):
                changes.append(
                    Change(
                        "changed",
                        category,
                        target,
                        path,
                        field,
                        old.get(field),
                        new.get(field),
                    )
                )
    return tuple(changes)
