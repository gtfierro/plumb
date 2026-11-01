"""Link a closure to canonical dependency symbols and explicit authoring views."""

from dataclasses import asdict

from .ir import ClassIR, SchemaIR
from .overlays import Overlay
from .symbols import Symbols


def link(ir: SchemaIR, dependency: Symbols, overlay: Overlay) -> None:
    """Reuse identical imports; represent changed projections as nominal subtypes."""
    # Alias unchanged imported classes; emit canonical views for refinements.
    # Policy changes also require a view to avoid modifying dependency classes.
    ir.dependencies = [
        {
            "module": dependency.module,
            "sha256": dependency.digest,
            "ontology": dependency.ontology,
        }
    ]
    policy_classes = {
        target.target if hasattr(target, "target") else target
        for target in overlay.rshift
    }
    if overlay.connector:
        policy_classes.add("http://data.ashrae.org/standard223#Connectable")
    for symbol in ir.classes:
        original = dependency.classes.get(symbol.iri)
        if original is None:
            continue
        if (
            _projection(symbol) == _projection(original)
            and symbol.iri not in policy_classes
            and symbol.name not in policy_classes
        ):
            symbol.python_module = original.python_module or dependency.module
            symbol.canonical_name = original.name
        else:
            symbol.canonical_module = (
                original.canonical_module or original.python_module or dependency.module
            )
            symbol.canonical_name = original.canonical_name or original.name
            # Canonical bases own their descriptors; views declare only the
            # additions/refinements that the original closure placed here.
            original_props = {
                prop.predicate: prop for prop in original.effective_props.values()
            }
            symbol.own_props = [
                prop
                for prop in symbol.own_props
                if prop.predicate not in original_props
                or _property(asdict(prop))
                != _property(asdict(original_props[prop.predicate]))
            ]
            symbol.cp_slots = [
                slot for slot in symbol.cp_slots if slot not in original.cp_slots
            ]
            original_constraints = [
                _expressions(asdict(expr)) for expr in original.cp_constraints
            ]
            symbol.cp_constraints = [
                expr
                for expr in symbol.cp_constraints
                if _expressions(asdict(expr)) not in original_constraints
            ]
            symbol.class_defaults = [
                item
                for item in symbol.class_defaults
                if item not in original.class_defaults
            ]
    by_name = {item.name: item.iri for item in ir.enums}
    dependency_names = {item.name: item.iri for item in dependency.enums.values()}
    for symbol in ir.enums:
        original = dependency.enums.get(symbol.iri)
        if original is None:
            continue
        if {by_name[name] for name in symbol.parents} != {
            dependency_names[name] for name in original.parents
        } or {by_name[name] for name in symbol.constituents} != {
            dependency_names[name] for name in original.constituents
        }:
            raise ValueError(
                f"{symbol.iri}: cannot redefine an imported enum hierarchy"
            )
        symbol.python_module = original.python_module or dependency.module
        symbol.python_name = original.python_name or original.name


def _projection(symbol: ClassIR) -> dict:
    """Compare behavior rather than documentation, aliases, or source labels."""
    item = asdict(symbol)
    properties = {}
    for prop in item["effective_props"].values():
        properties[prop["predicate"]] = _property(prop)
    return {
        "parents": sorted(symbol.parent_iris),
        "ancestors": sorted(symbol.ancestor_iris),
        "properties": properties,
        "slots": item["cp_slots"],
        "constraints": _expressions(item["cp_constraints"]),
        "abstract": symbol.abstract,
        "defaults": symbol.class_defaults,
        "maximum_ports": symbol.maximum_ports,
    }


def _property(prop: dict) -> dict:
    return {
        key: value
        for key, value in prop.items()
        if key not in {"label", "definition", "ranges", "sources"}
    }


def _expressions(value):
    if isinstance(value, dict):
        return {
            key: _expressions(item) for key, item in value.items() if key != "source"
        }
    if isinstance(value, list):
        return [_expressions(item) for item in value]
    return value
