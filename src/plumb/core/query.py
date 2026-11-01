"""Hydrate generated Python objects from RDF and select them."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from importlib import import_module
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote

import rdflib
from rdflib import RDF, RDFS, OWL, Literal, URIRef

from .entity import Entity
from .errors import ModelingError
from .meta import PropertySpec, Registry
from .terms import TermValue
from .traversal import matches as matches

if TYPE_CHECKING:
    from .model import Model


# Hydration preserves facts; construction creates authoring conveniences.
# Keep those operations separate: loading must not insert defaults, synthesize
# points, run containment hooks, or enforce constructor-only requirements.
# Strict mode controls which RDF values can be projected into Python. SHACL
# validation remains a separate operation on the full backing graph.
def load_graph(
    model_type: type[Model],
    source: rdflib.Graph | str | Path,
    *,
    registries: Registry | Iterable[Registry] | None,
    namespace: str | None,
    infer: bool,
    shapes: rdflib.Graph | str | Path | None,
    strict: bool,
) -> Model:
    """Build a Model whose generated objects write through to ``source``."""
    graph = _read_graph(source)
    registry_list = (
        _discover_registries(graph)
        if registries is None
        else (registries,)
        if isinstance(registries, Registry)
        else tuple(registries)
    )
    if not registry_list:
        raise ValueError("at least one generated package registry is required")
    # Resolve the selected symbol set before inference can mutate the input.
    # Canonical classes cannot know their future extension terms and enums.
    symbols = Registry.compose(registry_list)
    if infer:
        import shifty

        if shapes is None:
            # Like validate(): the rules ship with the generated packages,
            # not with the model graph being loaded.
            from .validation import shapes_for

            shapes = shapes_for(
                [cls for registry in registry_list for cls in registry.classes],
                registry_list,
            )
        inferred = shifty.infer(graph, shapes).graph()
        if isinstance(source, rdflib.Graph):
            graph += inferred
        else:
            graph = inferred

    model = model_type(namespace or _infer_namespace(graph, symbols.by_iri))
    model._loaded_graph = graph
    model._loaded_registries = registry_list
    by_node: dict[URIRef, Entity] = {}

    # Allocate all typed resources before reading properties. A relation may
    # point forward in iteration order, or close a cycle, and every occurrence
    # of a given resource must resolve to the very same Python object.
    subjects = sorted(set(graph.subjects(RDF.type)), key=str)
    for subject in subjects:
        if not isinstance(subject, URIRef):
            continue
        candidates: list[type[Entity]] = []
        for rdf_type in graph.objects(subject, RDF.type):
            if (candidate := symbols.by_iri.get(str(rdf_type))) is not None:
                candidates.append(candidate)
        entity_type = _most_specific(subject, candidates, strict=strict)
        if entity_type is None:
            continue
        entity = entity_type.__new__(entity_type)
        label_node = next(iter(graph.objects(subject, RDFS.label)), None)
        comment_node = next(iter(graph.objects(subject, RDFS.comment)), None)
        entity._label = str(label_node) if label_node is not None else None
        entity._comment = str(comment_node) if comment_node is not None else None
        entity._data = {}
        entity._rels = {}
        entity._named_points = {}
        name = _local_name(str(subject))
        if entity._label is None:
            entity._label = name
        model._bind_loaded(entity, str(subject), name)
        by_node[subject] = entity
        managed = model._managed_triples.setdefault(str(subject), set())
        managed.add((subject, RDF.type, URIRef(entity_type.meta.iri)))
        if label_node is not None:
            managed.add((subject, RDFS.label, label_node))
        if comment_node is not None:
            managed.add((subject, RDFS.comment, comment_node))

    for subject, entity in by_node.items():
        specs = {
            spec.predicate: spec for spec in type(entity)._effective_specs().values()
        }
        for predicate, spec in specs.items():
            values = list(graph.objects(subject, URIRef(predicate)))
            if not values:
                continue
            converted: list[object] = []
            accepted_nodes: list[rdflib.term.Node] = []
            for value in values:
                item = _convert_value(
                    graph,
                    value,
                    spec,
                    symbols,
                    by_node,
                    strict=strict,
                )
                if item is _SKIP:
                    continue
                converted.append(item)
                accepted_nodes.append(value)
            managed_count = _store_values(
                entity,
                spec,
                converted,
                strict=strict,
            )
            # Own only the triples actually represented by the projection.
            # In permissive mode a scalar may accept one of several RDF values;
            # later edits may replace that managed value, but must preserve the
            # extra values and unknown RDF the loader did not understand.
            for value in accepted_nodes[:managed_count]:
                model._managed_triples[str(subject)].add(
                    (subject, URIRef(predicate), value)
                )

    for entity in model.entities:
        declarations = getattr(type(entity), "_point_declarations", {})
        if declarations:
            domain = entity.meta.registry._domain
            if domain is None:
                raise ModelingError("named points require a connection domain")
            domain.restore(entity, strict=strict)
    return model


#: Installed packages, domain configurations included, that a graph's
#: ``owl:imports`` can select.
_PACKAGES = (
    "watr",
    "watr.asm2d",
    "watr.drinking_water",
    "watr.seawater_ro",
    "s223",
    "s223.hvac",
    "brick",
    "qudt",
)


def _ontology_key(iri: str) -> str:
    # ``dw:`` and ``<…/drinking-water>`` name the same ontology.
    return iri.rstrip("#/")


def _discover_registries(graph: rdflib.Graph) -> tuple[Registry, ...]:
    """Select installed packages from the model ontology's imports."""
    imports = {
        _ontology_key(str(dependency))
        for ontology in graph.subjects(RDF.type, OWL.Ontology)
        for dependency in graph.objects(ontology, OWL.imports)
    }
    candidates: list[Registry] = []
    for package in _PACKAGES:
        module = import_module(f"plumb.{package}")
        registry: Registry = module._REGISTRY
        identity = registry.ontology
        ontology_iri = identity.iri or identity.source
        if ontology_iri is None or _ontology_key(ontology_iri) not in imports:
            continue
        declared_versions = (
            {
                str(version)
                for version in graph.objects(URIRef(identity.iri), OWL.versionInfo)
            }
            if identity.iri
            else set()
        )
        if declared_versions and identity.version not in declared_versions:
            raise ValueError(
                f"{identity.name} ontology version in graph is "
                f"{', '.join(sorted(declared_versions))}, but the installed "
                f"package has {identity.version or 'no version'}"
            )
        candidates.append(registry)
    if not candidates:
        raise ValueError(
            "no installed ontology package matches this graph's owl:imports; "
            "pass registries= explicitly"
        )
    return tuple(
        registry
        for registry in candidates
        if not any(
            registry is not other and set(registry.by_iri) < set(other.by_iri)
            for other in candidates
        )
    )


def _read_graph(source: rdflib.Graph | str | Path) -> rdflib.Graph:
    if isinstance(source, rdflib.Graph):
        return source
    graph = rdflib.Graph()
    graph.parse(str(source))
    return graph


def _most_specific(
    subject: URIRef,
    candidates: list[type[Entity]],
    *,
    strict: bool,
) -> type[Entity] | None:
    candidates = list(dict.fromkeys(candidates))
    if not candidates:
        return None
    most_specific = [
        candidate
        for candidate in candidates
        if all(issubclass(candidate, other) for other in candidates)
    ]
    if len(most_specific) == 1:
        return most_specific[0]
    if strict:
        names = ", ".join(sorted(candidate.__name__ for candidate in candidates))
        raise ModelingError(
            f"{subject} has incompatible generated Python types: {names}"
        )
    return max(candidates, key=lambda candidate: len(candidate.__mro__))


def _convert_value(
    graph: rdflib.Graph,
    value: rdflib.term.Node,
    spec: PropertySpec,
    registry: Registry,
    by_node: Mapping[URIRef, Entity],
    *,
    strict: bool,
) -> object:
    if spec.kind == "literal":
        if isinstance(value, Literal):
            return value.toPython()
        return _bad_value(value, spec, "an RDF literal", strict=strict)

    if spec.kind == "object":
        if isinstance(value, URIRef):
            if value in by_node:
                return by_node[value]
            compiled = _reference_terms().get(str(value))
            if compiled is not None:
                return compiled
            return _bad_value(
                value,
                spec,
                "a resource with a generated Python type (include its registry)",
                strict=strict,
            )
        return _bad_value(
            value,
            spec,
            "a resource with a generated Python type",
            strict=strict,
        )

    if spec.kind == "class":
        if isinstance(value, URIRef):
            generated_class = registry.by_iri.get(str(value))
            if generated_class is not None:
                return generated_class
        return _bad_value(value, spec, "a registered ontology class", strict=strict)

    if spec.kind == "enum":
        if isinstance(value, URIRef):
            try:
                return registry.resolve_enum(str(value))
            except KeyError:
                return _bad_value(value, spec, "a registered enum value", strict=strict)
        return _bad_value(value, spec, "a registered enum value", strict=strict)

    if spec.kind == "term":
        if isinstance(value, URIRef):
            known = registry.terms_by_iri.get(str(value)) or _reference_terms().get(
                str(value)
            )
            if known is not None:
                return known
            return _term(graph, value)
        return _bad_value(value, spec, "a named RDF resource", strict=strict)

    if isinstance(value, Literal):
        return value
    if isinstance(value, URIRef):
        if value in by_node:
            return by_node[value]
        return _term(graph, value)
    return _bad_value(value, spec, "a literal or named RDF resource", strict=strict)


def _bad_value(
    value: rdflib.term.Node,
    spec: PropertySpec,
    expected: str,
    *,
    strict: bool,
) -> object:
    if strict:
        raise ModelingError(
            f"cannot load {value.n3()} as {spec.name}: expected {expected}"
        )
    return _SKIP


def _store_values(
    entity: Entity,
    spec: PropertySpec,
    values: list[object],
    *,
    strict: bool,
) -> int:
    if not values:
        return 0
    many = spec.max_count != 1 and spec.kind in {"object", "class", "enum"}
    if many:
        if spec.kind in {"object", "class"}:
            entity._store_for(spec)._items.extend(values)
        else:
            entity._data[spec.name] = values
        return len(values)
    if len(values) > 1 and strict:
        raise ModelingError(
            f"{entity.meta.instance_iri} has {len(values)} values for scalar "
            f"property {spec.name}"
        )
    entity._data[spec.name] = values[0]
    return 1


@lru_cache(maxsize=1)
def _reference_terms() -> dict[str, TermValue]:
    """Installed external named individuals, shared rather than hydrated locally."""
    from plumb.qudt import units, quantity_kinds

    return {
        term.iri: term
        for module in (units, quantity_kinds)
        for term in vars(module).values()
        if isinstance(term, TermValue)
    }


def _term(graph: rdflib.Graph, value: URIRef) -> TermValue:
    known = _reference_terms().get(str(value))
    if known is not None:
        return known
    return TermValue(
        str(value),
        label=_first_text(graph.objects(value, RDFS.label)),
        types=tuple(str(rdf_type) for rdf_type in graph.objects(value, RDF.type)),
    )


def _first_text(values: Iterable[rdflib.term.Node]) -> str | None:
    return next((str(value) for value in values), None)


def _local_name(iri: str) -> str:
    local = iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1].rsplit(":", 1)[-1]
    return unquote(local) or iri


def _infer_namespace(
    graph: rdflib.Graph,
    classes_by_iri: Mapping[str, type[Entity]],
) -> str:
    namespaces: Counter[str] = Counter()
    for subject in set(graph.subjects(RDF.type)):
        if not isinstance(subject, URIRef):
            continue
        if not any(
            str(rdf_type) in classes_by_iri
            for rdf_type in graph.objects(subject, RDF.type)
        ):
            continue
        iri = str(subject)
        if "#" in iri:
            namespaces[iri.rsplit("#", 1)[0] + "#"] += 1
        elif "/" in iri:
            namespaces[iri.rsplit("/", 1)[0] + "/"] += 1
    if namespaces:
        return namespaces.most_common(1)[0][0]
    return "urn:plumb:loaded#"


_SKIP = object()
