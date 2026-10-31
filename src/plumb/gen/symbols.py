"""Compiler dependency metadata, read without executing generated packages.

The export contains semantic ancestry and effective constraints, independently
of Python's MRO and runtime registries. Callers load one dependency; file lookup,
format checking, and symbol decoding stay here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from importlib.machinery import PathFinder
import json
from pathlib import Path
from typing import Any

from .ir import ClassIR, CPConstraintIR, CPSlotIR, EnumIR, PropIR, SchemaIR

FILENAME = "_symbols.json"
FORMAT = 1


@dataclass
class Symbols:
    ontology: dict[str, Any]
    classes: dict[str, ClassIR]
    enums: dict[str, EnumIR]
    module: str
    digest: str

    @classmethod
    def load(cls, module: str) -> Symbols:
        """Read a generated package's export without importing that package."""
        locations = None
        for part in _module_parts(module):
            spec = PathFinder.find_spec(part, locations)
            if spec is None or spec.submodule_search_locations is None:
                raise ValueError(f"{module}: compiler dependency package not found")
            locations = list(spec.submodule_search_locations)
        assert locations is not None
        path = Path(locations[0]) / FILENAME
        try:
            data = path.read_text()
        except FileNotFoundError:
            raise ValueError(
                f"{module}: missing compiler dependency export {path}; "
                "regenerate the base package"
            ) from None
        return cls.decode(data, module=module, source=str(path))

    @classmethod
    def decode(cls, text: str, *, module: str, source: str = "dependency") -> Symbols:
        """Validate the export format and reconstruct compiler symbols."""
        try:
            data = json.loads(text)
            if data.get("format") != FORMAT:
                raise ValueError(
                    f"unsupported compiler dependency format {data.get('format')!r}"
                )
            properties = {
                key: _property(value) for key, value in data["properties"].items()
            }
            classes = {}
            for item in data["classes"]:
                item = dict(item)
                item["effective_props"] = {
                    properties[key].name: properties[key]
                    for key in item.pop("properties")
                }
                item["cp_slots"] = [_slot(slot) for slot in item["cp_slots"]]
                item["cp_constraints"] = [
                    _expression(expr) for expr in item["cp_constraints"]
                ]
                for key in ("parents", "parent_iris", "ancestor_iris"):
                    item[key] = tuple(item[key])
                item["class_defaults"] = [
                    tuple(pair) for pair in item["class_defaults"]
                ]
                symbol = ClassIR(**item)
                if symbol.iri in classes:
                    raise ValueError(f"duplicate class identity {symbol.iri}")
                classes[symbol.iri] = symbol
            enums = {}
            for item in data["enums"]:
                item = dict(item)
                for key in ("parents", "constituents"):
                    item[key] = tuple(item[key])
                symbol = EnumIR(**item)
                enums[symbol.iri] = symbol
            return cls(
                data["ontology"],
                classes,
                enums,
                module,
                hashlib.sha256(text.encode()).hexdigest(),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"{source}: invalid compiler dependency: {error}"
            ) from error


def export_symbols(ir: SchemaIR, *, graph_digest: str) -> str:
    """Emit deterministic dependency symbols; Python classes are not inspected."""
    classes = []
    properties: dict[str, Any] = {}
    for symbol in sorted(ir.classes, key=lambda item: item.iri):
        item = asdict(symbol)
        item.pop("own_props")
        item.pop("effective_props")
        item["properties"] = []
        for name in sorted(symbol.effective_props):
            prop = asdict(symbol.effective_props[name])
            key = hashlib.sha256(json.dumps(prop, sort_keys=True).encode()).hexdigest()
            properties[key] = prop
            item["properties"].append(key)
        classes.append(item)
    return (
        json.dumps(
            {
                "format": FORMAT,
                "ontology": {
                    "name": ir.ontology_name,
                    "iri": ir.ontology_iri,
                    "version": ir.version,
                    "source": ir.source,
                },
                "graph_sha256": graph_digest,
                "classes": classes,
                "properties": properties,
                "enums": [
                    asdict(symbol)
                    for symbol in sorted(ir.enums, key=lambda item: item.iri)
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _module_parts(module: str) -> list[str]:
    parts = module.split(".")
    if not parts or any(not part.isidentifier() for part in parts):
        raise ValueError(f"invalid dependency module name {module!r}")
    return [".".join(parts[:index]) for index in range(1, len(parts) + 1)]


def _property(item: dict[str, Any]) -> PropIR:
    item = dict(item)
    for key in ("ranges", "sources", "enum_ranges"):
        item[key] = tuple(item[key])
    item["range_groups"] = tuple(tuple(group) for group in item["range_groups"])
    return PropIR(**item)


def _slot(item: dict[str, Any]) -> CPSlotIR:
    item = dict(item)
    item["medium_options"] = tuple(item["medium_options"])
    return CPSlotIR(**item)


def _expression(item: dict[str, Any]) -> CPConstraintIR:
    item = dict(item)
    item["slot"] = _slot(item["slot"]) if item["slot"] is not None else None
    item["children"] = [_expression(child) for child in item["children"]]
    return CPConstraintIR(**item)
