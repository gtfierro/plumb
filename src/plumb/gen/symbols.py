"""Compiler dependency metadata, read without executing generated packages.

The export contains semantic ancestry and effective constraints, independently
of Python's MRO and runtime registries. Callers load one dependency; file lookup,
format checking, and symbol decoding stay here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import hashlib
from importlib.machinery import PathFinder
import json
from pathlib import Path
from typing import Any

from rdflib.util import from_n3

from .ir import ClassIR, CPConstraintIR, CPSlotIR, EnumIR, PointIR, PropIR, SchemaIR

FILENAME = "_symbols.json"
FORMAT = 3


@dataclass
class Symbols:
    ontology: dict[str, Any]
    classes: dict[str, ClassIR]
    enums: dict[str, EnumIR]
    module: str
    digest: str
    dependencies: list[dict[str, Any]] = field(default_factory=list)
    term_types: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def imported_classes(self) -> dict[str, ClassIR]:
        """Keep each symbol's defining module when another package re-exports it."""
        return {
            iri: replace(symbol, python_module=symbol.python_module or self.module)
            for iri, symbol in self.classes.items()
        }

    @classmethod
    def load(cls, module: str, _active: frozenset[str] = frozenset()) -> Symbols:
        """Read a generated package's export without importing that package."""
        if module in _active:
            raise ValueError(f"{module}: cyclic compiler dependency")
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
        symbols = cls.decode(data, module=module, source=str(path))
        classes, enums, term_types = {}, {}, {}
        for record in symbols.dependencies:
            dependency = cls.load(record["module"], _active | {module})
            if dependency.digest != record["sha256"]:
                raise ValueError(
                    f"{module}: compiler dependency {dependency.module} changed; "
                    "regenerate the dependent package"
                )
            for iri, symbol in dependency.imported_classes().items():
                if iri in classes and classes[iri] != symbol:
                    previous = classes[iri]
                    if (symbol.canonical_module, symbol.canonical_name) == (
                        previous.python_module,
                        previous.name,
                    ):
                        pass
                    elif (previous.canonical_module, previous.canonical_name) == (
                        symbol.python_module,
                        symbol.name,
                    ):
                        continue
                    else:
                        raise ValueError(
                            f"{module}: incompatible dependency symbol {iri}"
                        )
                classes[iri] = symbol
            for iri, symbol in dependency.enums.items():
                imported = replace(
                    symbol, python_module=symbol.python_module or dependency.module
                )
                if iri in enums and enums[iri] != imported:
                    raise ValueError(f"{module}: incompatible dependency enum {iri}")
                enums[iri] = imported
            term_types.update(dependency.term_types)
        local = {
            iri: item
            for iri, item in symbols.classes.items()
            if item.canonical_module is None
        }
        views = {
            iri: item
            for iri, item in symbols.classes.items()
            if item.canonical_module is not None
        }
        if set(classes).intersection(local):
            raise ValueError(f"{module}: cannot redefine an imported class identity")
        for iri, view in views.items():
            canonical = classes.get(iri)
            if canonical is None or (view.canonical_module, view.canonical_name) != (
                canonical.canonical_module or canonical.python_module,
                canonical.canonical_name or canonical.name,
            ):
                raise ValueError(f"{module}: unlinked canonical class for view {iri}")
        symbols.classes = classes | local | views
        if enums.keys() & symbols.enums.keys():
            raise ValueError(f"{module}: cannot redefine an imported enum identity")
        symbols.enums = enums | symbols.enums
        symbols.term_types = term_types | symbols.term_types
        return symbols

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
            for item in [*data["classes"], *data["views"]]:
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
                item["points"] = [PointIR(**point) for point in item.get("points", [])]
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
                data.get("dependencies", []),
                {
                    iri: tuple(types)
                    for iri, types in data.get("term_types", {}).items()
                },
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"{source}: invalid compiler dependency: {error}"
            ) from error


def export_symbols(ir: SchemaIR, *, graph_digest: str) -> str:
    """Emit deterministic dependency symbols; Python classes are not inspected."""
    classes, views = [], []
    properties: dict[str, Any] = {}
    for symbol in sorted(ir.classes, key=lambda item: item.iri):
        if symbol.python_module is not None:
            continue
        item = asdict(symbol)
        item.pop("own_props")
        item.pop("effective_props")
        item["properties"] = []
        for name in sorted(symbol.effective_props):
            prop = asdict(symbol.effective_props[name])
            for key in ("required_values", "default_values", "choices"):
                prop[key] = (
                    [value.n3() for value in prop[key]]
                    if prop[key] is not None
                    else None
                )
            key = hashlib.sha256(json.dumps(prop, sort_keys=True).encode()).hexdigest()
            properties[key] = prop
            item["properties"].append(key)
        (views if symbol.canonical_module else classes).append(item)
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
                "dependencies": ir.dependencies,
                "term_types": ir.term_types,
                "classes": classes,
                "views": views,
                "properties": properties,
                "enums": [
                    asdict(symbol)
                    for symbol in sorted(ir.enums, key=lambda item: item.iri)
                    if symbol.python_module is None
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
    for key in ("ranges", "sources", "enum_ranges", "term_ranges"):
        if key not in item:
            continue
        item[key] = tuple(item[key])
    for key in ("required_values", "default_values", "choices"):
        if key in item and item[key] is not None:
            item[key] = tuple(from_n3(value) for value in item[key])
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
