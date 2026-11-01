"""The plumb compiler: ontology + SHACL -> generated Python package.

Pipeline: load the ontology graph (with its imports closure, resolved by
ontoenv when fetching by IRI), extract a plain intermediate representation
(``schema.extract``), then render Python source (``emit.emit_module``) with
optional UX overlays (``overlays``).
"""

from __future__ import annotations

from pathlib import Path
import hashlib

import rdflib

from . import overlays
from .diagnostics import FILENAME as SUPPORT_FILE, CompilationError, support_report
from .emit import emit_enums_module, emit_module
from .schema import SchemaIR, extract

__all__ = [
    "CompilationError",
    "SchemaIR",
    "compile_modules",
    "compile_source",
    "extract",
    "generate",
    "overlays",
]


def _resolve_overlay(
    name: str, overlay: overlays.Overlay | None | str
) -> overlays.Overlay | None:
    """``"auto"`` picks the built-in overlay matching ``name`` (if any)."""
    if overlay == "auto":
        return overlays.for_ontology(name)
    assert overlay is None or isinstance(overlay, overlays.Overlay)
    return overlay


def compile_modules(
    graph: rdflib.Graph,
    *,
    name: str,
    source: str | None = None,
    overlay: overlays.Overlay | None | str = "auto",
) -> dict[str, str]:
    """Compile an ontology graph to Python sources, keyed by file name.

    Always contains ``__init__.py``; ontologies with a punned enumeration
    hierarchy (the overlay's ``enum_root``) also get an ``enums.py``.
    """
    from .configurations import CODEGEN, compile_configurations

    if any(graph.objects(None, CODEGEN.baseModule)):
        if overlay not in ("auto", None):
            raise ValueError(
                "configuration packages inherit base policy; custom overlay bindings are not supported"
            )
        from rdflib.compare import to_canonical_graph

        canonical = to_canonical_graph(graph)
        modules = compile_configurations(canonical, name=name, source=source)
        modules["_shapes.ttl"] = (
            "\n".join(sorted(canonical.serialize(format="nt").splitlines())) + "\n"
        )
        return modules
    from .stable import stable_graph

    graph = stable_graph(graph)
    resolved = _resolve_overlay(name, overlay)
    ir = extract(
        graph,
        name=name,
        source=source,
        enum_root=resolved.enum_root if resolved else None,
        ontology_iri=resolved.ontology_iri if resolved else None,
        primary_namespace=resolved.primary_namespace if resolved else None,
        class_properties=resolved.class_properties if resolved else (),
        deferred_properties=resolved.deferred_properties if resolved else (),
    )
    bindings = overlays.resolve(resolved, ir, graph) if resolved is not None else None
    dependency = None
    if resolved is not None and resolved.base_module:
        from .linking import link
        from .symbols import Symbols

        dependency = Symbols.load(resolved.base_module)
        link(ir, dependency, resolved)
    modules = {"__init__.py": emit_module(ir, bindings, dependency=dependency)}
    modules[SUPPORT_FILE] = support_report(
        graph,
        ir.classes,
        bindings=bindings.diagnostics if bindings else (),
        connections=ir.connection_support,
    )
    # Keep validation reproducible: generated packages carry the exact graph
    # that their Python API and solver metadata were compiled from.
    modules["_shapes.ttl"] = str(graph.serialize(format="turtle"))
    from .symbols import FILENAME, export_symbols

    modules[FILENAME] = export_symbols(
        ir, graph_digest=hashlib.sha256(modules["_shapes.ttl"].encode()).hexdigest()
    )
    enums_source = emit_enums_module(ir)
    if enums_source:
        modules["enums.py"] = enums_source
    return modules


def compile_source(
    graph: rdflib.Graph,
    *,
    name: str,
    source: str | None = None,
    overlay: overlays.Overlay | None | str = "auto",
) -> str:
    """Compile to the main module's source (convenience for tests/tools)."""
    return compile_modules(graph, name=name, source=source, overlay=overlay)[
        "__init__.py"
    ]


def generate(
    graph: rdflib.Graph,
    out_dir: str | Path,
    *,
    name: str,
    source: str | None = None,
    overlay: overlays.Overlay | None | str = "auto",
) -> Path:
    """Compile and write a generated package; returns the package __init__."""
    out = Path(out_dir)
    modules = compile_modules(graph, name=name, source=source, overlay=overlay)
    from .artifacts import write_modules

    write_modules(modules, out)
    return out / "__init__.py"
