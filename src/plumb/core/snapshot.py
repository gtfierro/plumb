"""Snapshot ownership: copy authored state, preserve RDF, then freeze once."""

from __future__ import annotations

from typing import Any

import rdflib

from .entity import Entity
from .model import Model
from .points import PointGroupRef, PointRef
from .relations import RelSet
from .resolution import ResolutionExplanation, ResolvedModel


class Snapshot:
    """An isolated mutable build of a model, owned by the runtime core.

    A domain may add derived objects and decisions. It does not clone or freeze
    the source, and failures discard this build without changing authored state.
    """

    def __init__(self, source: Model) -> None:
        self.source = source
        self._source_revision = source._revision
        self.model = Model(
            source.namespace,
            name=source.name,
            ontology_iri=source.ontology_iri,
            imports=source.imports,
            prefixes=source.prefixes,
        )
        self.model._resolving = True
        self.model._loaded_registries = source._loaded_registries
        self.entities: dict[Entity, Entity] = {}
        self.connections: dict[int, Entity] = {}
        self.explanations: dict[int, ResolutionExplanation] = {}
        # Allocate all shells before remapping links, including cycles.
        # Bypass constructors to avoid applying defaults and hooks during copying.
        for entity in source.entities:
            copied = object.__new__(type(entity))
            copied.__dict__.update(entity.__dict__)
            copied._data = {}
            copied._rels = {}
            copied._named_points = {}
            self.model._bind_loaded(copied, entity._iri, entity.name)
            self.entities[entity] = copied
        for entity, copied in self.entities.items():
            copied._data = self.copy(entity._data)
            if source._loaded_graph is not None:
                copied._named_points = self.copy(entity._named_points)
            for name, store in entity._rels.items():
                new_store = RelSet(copied, store._spec)
                new_store._items = self.copy(store._items)
                copied._rels[name] = new_store
        if source._loaded_graph is not None:
            # Copy backing RDF to retain facts outside the Python projection.
            graph = rdflib.Graph()
            for prefix, namespace in source._loaded_graph.namespaces():
                graph.bind(prefix, namespace, replace=True)
            graph += source._loaded_graph
            self.model._loaded_graph = graph
            self.model._managed_triples = {
                iri: set(triples) for iri, triples in source._managed_triples.items()
            }

    def copy(self, value: Any) -> Any:
        """Copy containers and remap entity references into this snapshot."""
        if isinstance(value, PointRef):
            return PointRef(self.copy(value.owner), value.name, self.copy(value._port))
        if isinstance(value, PointGroupRef):
            return PointGroupRef(
                self.copy(value.owner), value.name, self.copy(value.points)
            )
        if isinstance(value, Entity):
            return self.entities.get(value, value)
        if isinstance(value, dict):
            return {self.copy(key): self.copy(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.copy(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.copy(item) for item in value)
        if isinstance(value, set):
            return {self.copy(item) for item in value}
        if isinstance(value, frozenset):
            return frozenset(self.copy(item) for item in value)
        return value

    def finish(self) -> ResolvedModel:
        """Restore references and publish a frozen snapshot at the source revision."""
        from .errors import ModelingError
        from .lifecycle import domain_for

        if self.source._revision != self._source_revision:
            raise ModelingError("model changed while its snapshot was being built")

        domain = domain_for(self.model)
        if domain is not None:
            domain.finish_snapshot(self.model)
        # ResolvedModel freezes the build; Model.resolve() caches it on success.
        self.model._resolving = False
        self.model._revision = self._source_revision
        result = ResolvedModel(
            self.model,
            self.connections,
            self.explanations,
            self._source_revision,
            authored_model=self.source,
        )
        self.model._resolved_cache = result
        return result
