"""SHACL validation (via shifty), reported in Python terms.

The report translator does one job: turn a standard SHACL validation report
graph into :class:`Issue` objects that name *entities and attributes*, not
focus nodes and IRIs. Users should be able to read an issue and know which
line of their authoring script to fix.

shifty also exposes a structured result API (``validate_algebra``); we use
the W3C-report path for now because its vocabulary is stable, and revisit
once the structured API covers result paths end-to-end.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any

import rdflib
from rdflib import RDF
from rdflib.namespace import SH

from .terms import TermValue

if TYPE_CHECKING:
    from .entity import Entity
    from .meta import Registry
    from .model import Model


@dataclass(frozen=True)
class Issue:
    """One validation result, mapped back to the authoring layer."""

    severity: str
    """``violation`` | ``warning`` | ``info``."""

    message: str
    """Human-readable description (SHACL ``resultMessage``)."""

    entity: Entity | None
    """The entity the result focuses on, when it maps to one."""

    focus: str | None
    """The raw focus node IRI (useful when ``entity`` is None)."""

    path: str | None
    """The offending property path (IRI), if reported."""

    def __str__(self) -> str:
        where = (
            f"{self.entity.name} ({type(self.entity).__name__})"
            if self.entity is not None
            else self.focus or "<model>"
        )
        prop = f" [{_local(self.path)}]" if self.path else ""
        return f"{self.severity}: {where}{prop}: {self.message}"

    def _repr_pretty_(self, printer: Any, cycle: bool) -> None:
        # IPython and Jupyter display the readable form; repr() keeps fields.
        printer.text(str(self))


@dataclass(frozen=True)
class ValidationReport:
    """Outcome of :meth:`Model.validate`.

    Truthy when there are no *violations*; warnings/infos (223 uses info
    severity for advisory notices like dangling boundary connection points)
    are listed in ``issues`` but don't fail the model.
    """

    ok: bool
    issues: tuple[Issue, ...]

    @property
    def violations(self) -> tuple[Issue, ...]:
        return tuple(i for i in self.issues if i.severity == "violation")

    def __bool__(self) -> bool:
        return self.ok

    def __str__(self) -> str:
        if not self.issues:
            return "conforms"
        return "\n".join(str(issue) for issue in self.issues)

    def _repr_pretty_(self, printer: Any, cycle: bool) -> None:
        # IPython and Jupyter display the readable form; repr() keeps fields.
        printer.text(str(self))


def validate_model(
    model: Model, shapes: object = None, *, infer: bool = True
) -> ValidationReport:
    """Run shifty over the model's graph and map results to entities.

    ``shapes`` may be an rdflib Graph, a Turtle file path/URL, or None; with
    None, the ontology sources of the generated packages present in the model
    are used (each package's Registry knows its ontology's source).
    """
    import shifty

    shapes_graph = _resolve_shapes(model, shapes)
    if model._loaded_graph is not None:
        data_graph = model.graph()
        fallback = None
    else:
        snapshot = model.resolve()
        data_graph = snapshot.graph()
        fallback = snapshot._model
    conforms, report, _text = shifty.validate(data_graph, shapes_graph, infer=infer)
    issues = tuple(_issues_from_report(model, report, fallback=fallback))
    ok = bool(conforms) or not any(i.severity == "violation" for i in issues)
    return ValidationReport(ok=ok, issues=issues)


def _resolve_shapes(model: Model, shapes: object) -> rdflib.Graph:
    """Normalize the ``shapes`` argument to an rdflib Graph."""
    if isinstance(shapes, rdflib.Graph):
        return shapes
    if isinstance(shapes, (str, Path)):
        g = rdflib.Graph()
        g.parse(str(shapes))
        return g
    if shapes is None:
        return _package_shapes(model)
    raise TypeError(
        f"shapes must be a Graph, path/URL, or None; got {type(shapes).__name__}"
    )


def shapes_for(classes: Iterable[type], registries: Iterable[Registry]) -> rdflib.Graph:
    """The shapes (and SHACL-AF rules) of the packages defining ``classes``.

    Prefers each package's bundled ``_shapes.ttl``, falling back to the
    ontology source it records, and adds extension packages' schema graphs.
    """
    package_files: set[Path] = set()
    sources: set[str] = set()
    pending = list(registries)
    for entity_type in classes:
        for cls in entity_type.__mro__:
            if "_classinfo" not in cls.__dict__:
                continue
            registry = cls.__dict__["_classinfo"].registry
            pending.append(registry)
            if registry.schema_graph is not None:
                # This is the authoritative bundle, already parsed by the
                # package. Parsing its file again would duplicate anonymous
                # shape/list nodes rather than simply deduplicating triples.
                continue
            module = sys.modules.get(cls.__module__)
            module_file = getattr(module, "__file__", None)
            bundled = (
                Path(module_file).with_name("_shapes.ttl") if module_file else None
            )
            if bundled is not None and bundled.exists():
                package_files.add(bundled)
            source = cls.__dict__["_classinfo"].ontology.source
            if source is not None and (bundled is None or not bundled.exists()):
                sources.add(source)
    selected: set[Registry] = set()
    while pending:
        registry = pending.pop()
        if registry in selected:
            continue
        selected.add(registry)
        pending.extend(registry._dependencies)
    schemas = [
        schema
        for registry in selected
        if (schema := getattr(registry, "schema_graph", None)) is not None
    ]
    if not package_files and not sources and not schemas:
        raise ValueError(
            "no shapes given and no generated package in this model "
            "records an ontology source; pass shapes= explicitly"
        )
    g = rdflib.Graph()
    for schema in schemas:
        for triple in schema:
            g.add(triple)
    for package_file in sorted(package_files):
        g.parse(package_file)
    for source in sorted(sources):
        g.parse(source)
    return g


def _package_shapes(model: Model) -> rdflib.Graph:
    """Collect shapes from the ontology sources of the packages in use.

    Each generated package records where its ontology was loaded from
    (``OntologyInfo.source``); we parse the union of the distinct sources.
    """
    g = shapes_for(
        [type(entity) for entity in model.entities],
        {
            *model._loaded_registries,
            *(entity.meta.registry for entity in model.entities),
        },
    )
    # Vocabulary references carry authoritative types compiled from their
    # catalogs. A base package's bundled closure need not contain every unit
    # or quantity-kind individual referenced by the model.
    for entity in model:
        for _spec, value in entity._property_values():
            if isinstance(value, TermValue):
                for class_iri in value.types:
                    g.add(
                        (rdflib.URIRef(value.iri), RDF.type, rdflib.URIRef(class_iri))
                    )
    return g


def _issues_from_report(
    model: Model, report: rdflib.Graph, *, fallback: Model | None = None
):
    """Yield an Issue per ``sh:ValidationResult`` in a report graph."""
    for result in report.subjects(RDF.type, SH.ValidationResult):
        focus = report.value(result, SH.focusNode)
        severity = report.value(result, SH.resultSeverity)
        path = report.value(result, SH.resultPath)
        messages = [str(m) for m in report.objects(result, SH.resultMessage)]
        focus_iri = str(focus) if focus is not None else None
        entity = model._by_iri.get(focus_iri) if focus_iri else None
        if entity is None and focus_iri and fallback is not None:
            entity = fallback._by_iri.get(focus_iri)
        yield Issue(
            severity=_local(str(severity)).lower() if severity else "violation",
            message="; ".join(messages) or "constraint violated",
            entity=entity,
            focus=focus_iri,
            path=str(path) if path is not None else None,
        )


def _local(iri: str | None) -> str:
    """Local name of an IRI, for compact display."""
    if iri is None:
        return ""
    for sep in ("#", "/"):
        if sep in iri:
            return iri.rsplit(sep, 1)[1]
    return iri
