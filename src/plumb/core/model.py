"""The Model: the session object that collects entities and emits RDF.

A Model owns entity identity, authored state, and serialization. RDF hydration
and validation live in neighboring modules. Users interact with it three ways:

- ``with Model("urn:ex/bldg#") as m:`` — ambient binding; entities created
  inside the block belong to ``m`` without passing it around;
- ``m.save("bldg.ttl")`` — serialize;
- ``m.validate()`` — SHACL validation (via shifty) with errors mapped back
  to Python objects.
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from contextvars import ContextVar, Token
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable, Iterator, Mapping, TypeVar
from urllib.parse import quote

import rdflib
from rdflib import OWL, RDF, RDFS, Literal, URIRef

from .errors import ModelingError

if TYPE_CHECKING:
    from .entity import Entity
    from .enums import EnumValue
    from .meta import Registry
    from .points import PointGroupRef, PointRef
    from .resolution import (
        ConnectionHandle,
        PortHandle,
        ResolutionReport,
        ResolvedModel,
    )
    from .traversal import Exact
    from .validation import ValidationReport

#: The ambient model set by ``with Model(...)`` blocks.
_current: ContextVar[Model | None] = ContextVar("plumb_model", default=None)
_EntityT = TypeVar("_EntityT", bound="Entity")

#: The searched-type argument of the find methods: a class (subclasses
#: included), a tuple of classes, ``exact(cls)``, or ``None`` for any entity.
type EntityTypeFilter[T: Entity] = (
    type[T] | tuple[type[Entity] | Exact[type[Entity]], ...] | Exact[type[T]] | None
)


def current_model() -> Model | None:
    """The innermost active ``with Model(...)`` block, if any."""
    return _current.get()


class Model:
    """A model under construction: a namespace plus the entities in it."""

    def __init__(
        self,
        namespace: str,
        *,
        name: str | None = None,
        ontology_iri: str | None = None,
        imports: Iterable[str] = (),
        prefixes: Mapping[str, str] | None = None,
    ) -> None:
        """Create a model.

        ``namespace`` is the IRI prefix instance IRIs are minted under; a
        trailing ``#`` is added if it doesn't already end in ``#`` or ``/``.
        ``prefixes`` declares stable, readable RDF namespace bindings used
        during serialization.
        """
        if not namespace.endswith(("#", "/")):
            namespace += "#"
        self.namespace = namespace
        self.name = name
        self.ontology_iri = ontology_iri or namespace.rstrip("#/")
        self.imports = set(imports)
        self.prefixes = dict(prefixes or {})
        if "" in self.prefixes:
            raise ValueError("the default prefix is reserved for the model namespace")
        # State has three layers:
        #   entities/indexes       concrete authored objects and their identities
        #   *_intents              requests for objects that planning will create
        #   caches                 derived views, never the authoring authority
        # Reserving a future point/connection name prevents a later constructor
        # from taking an identity the planner has already promised to a handle.
        self.entities: list[Entity] = []
        self._by_name: dict[str, Entity] = {}
        self._by_iri: dict[str, Entity] = {}
        self._tokens: list[Token[Model | None]] = []
        self._auto_counters: dict[str, int] = {}
        self._connection_intents: list[ConnectionHandle] = []
        self._port_intents: list[PortHandle] = []
        self._system_intents: list[tuple[Entity, tuple[Entity, ...]]] = []
        self._reserved_names: set[str] = set()
        self._next_intent_id = 1
        self._revision = 0
        self._resolved_cache: ResolvedModel | None = None
        #: Containment and topology indexes (``plumb.core.traversal``).
        self._traversal_indexes: dict[str, Any] = {}
        self._plan_cache: dict[tuple[Any, ...], Any] = {}
        self._frozen = False
        self._resolving = False
        self._loaded_graph: rdflib.Graph | None = None
        # Selected schemas belong to the model, even if every hydrated entity
        # uses an imported canonical class rather than a local extension class.
        self._loaded_registries: tuple[Registry, ...] = ()
        self._managed_triples: dict[str, set[tuple[Any, Any, Any]]] = {}

    # -- ambient binding --------------------------------------------------

    @contextmanager
    def _atomic(self) -> Iterator[None]:
        """Roll back a compound authoring operation, including existing links."""

        self._assert_mutable()
        if self._resolving:
            # An unpublished snapshot build is discarded as a unit on failure.
            yield
            return
        # Preserve object identity while copying mutable containers. Replacing
        # existing entities with clones on rollback would strand references held
        # by callers and inverse relations. The journal restores stores on those
        # same objects, along with revisions and the previously published snapshot.
        loaded_triples = (
            set(self._loaded_graph) if self._loaded_graph is not None else None
        )
        attributes = {
            key: _copy_collections(value) for key, value in self.__dict__.items()
        }
        entities = {
            item: (
                _copy_collections(item._data),
                dict(item._rels),
                {key: list(store._items) for key, store in item._rels.items()},
                item.label,
                item.comment,
            )
            for item in self.entities
        }
        ports = {port: _copy_collections(port.__dict__) for port in self._port_intents}
        assignments = {
            handle: _copy_collections(handle.__dict__)
            for handle in self._connection_intents
        }
        try:
            yield
        except BaseException:
            self.__dict__.update(attributes)
            if loaded_triples is not None and self._loaded_graph is not None:
                self._loaded_graph.remove((None, None, None))
                for triple in loaded_triples:
                    self._loaded_graph.add(triple)
            for item, (data, relations, values, label, comment) in entities.items():
                item._data = data
                item._rels = relations
                item._label = label
                item._comment = comment
                for key, items in values.items():
                    item._rels[key]._items[:] = items
            for port, values in ports.items():
                port.__dict__.update(values)
            for handle, values in assignments.items():
                handle.__dict__.update(values)
            raise

    def __enter__(self) -> Model:
        self._tokens.append(_current.set(self))
        return self

    def __exit__(self, *exc_info: object) -> None:
        _current.reset(self._tokens.pop())

    def _bind(self, entity: Entity) -> None:
        """Mint an IRI for a new entity and index it. Called by Entity."""
        self._assert_mutable()
        if entity.name in self._by_name or entity.name in self._reserved_names:
            raise ModelingError(
                f"an entity named {entity.name!r} already exists in this "
                f"model ({self._by_name.get(entity.name, 'reserved')!r}); names must be "
                f"unique within a model"
            )
        entity._iri = self.namespace + quote(entity.name, safe="")
        self.entities.append(entity)
        self._by_name[entity.name] = entity
        self._by_iri[entity._iri] = entity
        self._touch(entity)

    def _bind_loaded(self, entity: Entity, iri: str, name: str) -> None:
        """Index an entity hydrated from an existing graph without minting an IRI."""
        candidate = name
        suffix = 2
        while candidate in self._by_name:
            candidate = f"{name}_{suffix}"
            suffix += 1
        entity._name = candidate
        entity._iri = iri
        entity._model = self
        self.entities.append(entity)
        self._by_name[candidate] = entity
        self._by_iri[iri] = entity

    def _unbind(self, entity: Entity) -> None:
        """Remove a partially constructed entity (failed __init__)."""
        self.entities.remove(entity)
        del self._by_name[entity.name]
        del self._by_iri[entity._iri]
        self._touch(entity)

    def _assert_mutable(self) -> None:
        if self._frozen:
            raise ModelingError("resolved model snapshots are immutable")

    def _touch(self, *entities: object) -> None:
        """Invalidate cached resolution after an authored mutation."""
        self._assert_mutable()
        self._revision += 1
        self._resolved_cache = None
        self._traversal_indexes = {}
        if self._loaded_graph is not None:
            self._sync_loaded_graph(*entities)

    def _sync_loaded_graph(self, *objects: object) -> None:
        """Replace touched objects' managed triples, preserving all other RDF."""
        if self._loaded_graph is None:  # pragma: no cover - caller invariant
            return
        from .entity import Entity as EntityBase

        touched: dict[str, Entity] = {}
        for obj in objects:
            entity = getattr(obj, "owner", obj)
            if isinstance(entity, EntityBase):
                touched[entity._iri] = entity
        for iri, entity in touched.items():
            # Replace our previous projection, not every outgoing RDF triple.
            # The rest of the graph belongs to its original author and may
            # contain predicates or values this package cannot represent.
            for triple in self._managed_triples.get(iri, ()):
                self._loaded_graph.remove(triple)
            current: set[tuple[Any, Any, Any]] = set()
            if self._by_iri.get(iri) is entity:
                current.update(self._entity_triples(entity))
                for triple in current:
                    self._loaded_graph.add(triple)
                self._managed_triples[iri] = current
            else:
                self._managed_triples.pop(iri, None)

    def _entity_triples(self, entity: Entity) -> Iterator[tuple[Any, Any, Any]]:
        """Yield the RDF projection controlled by one generated object."""
        subject = URIRef(entity._iri)
        yield subject, RDF.type, URIRef(entity._classinfo_effective().iri)
        yield subject, RDFS.label, Literal(entity.label)
        if entity.comment is not None:
            yield subject, RDFS.comment, Literal(entity.comment)
        for spec, value in entity._property_values():
            if spec.kind == "class":
                obj = URIRef(value.meta.iri)
            elif spec.kind == "object":
                obj = URIRef(value.iri if hasattr(value, "iri") else value._iri)
            elif spec.kind in {"enum", "term"}:
                obj = URIRef(value.iri)
            elif spec.kind == "value":
                if hasattr(value, "_iri"):
                    obj = URIRef(value._iri)
                elif hasattr(value, "iri"):
                    obj = URIRef(value.iri)
                else:
                    obj = Literal(value)
            else:
                obj = Literal(value)
            yield subject, URIRef(spec.predicate), obj

    def _assert_accepts_connections(self) -> None:
        """Deferred connections need an authored, mutable model."""
        self._assert_mutable()
        if self._loaded_graph is not None:
            raise ModelingError(
                "deferred S223/WaTr connections cannot yet be added to a "
                "graph-backed model; edit its concrete Connection and "
                "ConnectionPoint objects instead"
            )

    def _defer_connection(
        self,
        source: Entity | PortHandle | PointGroupRef,
        target: Entity | PortHandle | PointGroupRef,
        *,
        medium: EnumValue | None,
        connection: type[Entity] | None,
        name: str | None,
    ) -> ConnectionHandle:
        """Record an S223 connection intention without materializing it."""
        from .points import endpoint_owner
        from .resolution import ConnectionHandle

        self._assert_accepts_connections()
        source_owner = endpoint_owner(source)
        target_owner = endpoint_owner(target)
        if source_owner.meta.model is not self or target_owner.meta.model is not self:
            raise ModelingError("connection endpoints must belong to the same Model")
        base = name or f"{source.name}--{target.name}"
        reserved = base
        suffix = 2
        while reserved in self._by_name or reserved in self._reserved_names:
            if name is not None:
                raise ModelingError(
                    f"an entity or connection named {name!r} already exists"
                )
            reserved = f"{base}_{suffix}"
            suffix += 1
        handle = ConnectionHandle(
            self,
            self._next_intent_id,
            source,
            target,
            medium=medium,
            connection=connection,
            name=reserved,
        )
        self._next_intent_id += 1
        self._connection_intents.append(handle)
        self._reserved_names.add(reserved)
        self._touch(source, target)
        return handle

    def _defer_port(
        self,
        owner: Entity,
        name: str,
        direction: str | tuple[str, ...],
        *,
        medium: EnumValue | None,
        label: str | None = None,
        fixed_medium: bool = False,
    ) -> PortHandle:
        """Record a named connection point without choosing its medium."""
        from .resolution import PortHandle

        self._assert_mutable()
        if self._loaded_graph is not None:
            raise ModelingError(
                "deferred S223/WaTr ports cannot yet be added to a "
                "graph-backed model; create a concrete ConnectionPoint instead"
            )
        directions = (direction,) if isinstance(direction, str) else direction
        if not directions or not set(directions).issubset({"in", "out", "bi"}):
            raise ValueError(
                "port direction must be 'in', 'out', 'bi', or a non-empty tuple thereof"
            )
        if owner.meta.model is not self:
            raise ModelingError("port owner must belong to this Model")
        if name in self._by_name or name in self._reserved_names:
            raise ModelingError(f"an entity, port, or connection named {name!r} exists")
        port = PortHandle(
            self,
            owner,
            name,
            direction,
            medium=medium,
            label=label,
            fixed_medium=fixed_medium,
        )
        self._port_intents.append(port)
        self._reserved_names.add(name)
        self._touch(owner)
        return port

    def _auto_name(self, cls: type[Entity]) -> str:
        """Generate the next free ``<class>_<n>`` name for this model.

        The counter is per class-name prefix and only moves forward, but
        names a user minted manually (e.g. an explicit ``vav_2``) are
        skipped rather than collided with.
        """
        prefix = _snake(cls.__name__)
        counter = self._auto_counters.get(prefix, 0)
        while True:
            counter += 1
            candidate = f"{prefix}_{counter}"
            if candidate not in self._by_name and candidate not in self._reserved_names:
                break
        self._auto_counters[prefix] = counter
        return candidate

    def _unique_name(self, stem: str) -> str:
        """``stem`` if no entity, port, or connection uses it, else the first
        free ``stem-<n>``."""
        candidate, index = stem, 2
        while candidate in self._by_name or candidate in self._reserved_names:
            candidate = f"{stem}-{index}"
            index += 1
        return candidate

    def system(self, name: str, *, label: str | None = None) -> _SystemScope:
        """Collect equipment created in a scope into an S223 System."""
        if self._loaded_graph is not None:
            raise ModelingError(
                "deferred system scopes cannot yet be added to a graph-backed "
                "model; create a concrete System and edit has_member instead"
            )
        return _SystemScope(self, name, label=label)

    # -- lookup -----------------------------------------------------------

    def __getitem__(self, name: str) -> Entity:
        """Look an entity up by its local name or full instance IRI."""
        try:
            return self._by_name.get(name) or self._by_iri[name]
        except KeyError:
            raise KeyError(f"no entity named or identified by {name!r}") from None

    def __iter__(self) -> Iterator[Entity]:
        return iter(self.entities)

    def __len__(self) -> int:
        return len(self.entities)

    def by_class(self) -> dict[type[Entity], list[Entity]]:
        """Group current entities by their exact generated Python class.

        Keys are classes, so they can be imported and passed to ``find_all``.
        Values follow model insertion order. Deferred connections and ports
        appear only in a resolved snapshot, not in this authored inventory.
        """
        groups: dict[type[Entity], list[Entity]] = {}
        for entity in self.entities:
            groups.setdefault(type(entity), []).append(entity)
        return groups

    @classmethod
    def from_graph(
        cls,
        source: rdflib.Graph | str | Path,
        *,
        registries: Registry | Iterable[Registry] | None = None,
        namespace: str | None = None,
        infer: bool = False,
        shapes: rdflib.Graph | str | Path | None = None,
        strict: bool = True,
    ) -> Model:
        """Hydrate a mutable object model backed by an RDF graph.

        When ``registries`` is omitted, the loader selects installed ontology
        packages from the graph's ``owl:imports`` declarations. Pass a registry
        explicitly for graphs without those declarations or for custom
        packages, for example ``plumb.watr.drinking_water.REGISTRY``.
        When ``infer`` is true,
        shifty applies SHACL-AF rules before objects and their relationships
        are materialized; the rules come from ``shapes`` or, by default, the
        selected packages' bundled shapes, as in :meth:`validate`. Mutating generated attributes writes through to the
        graph; RDF outside the generated object projection is preserved.
        Unknown RDF classes remain in :meth:`graph` but are not exposed as
        Python objects.
        """
        from .query import load_graph

        return load_graph(
            cls,
            source,
            registries=registries,
            namespace=namespace,
            infer=infer,
            shapes=shapes,
            strict=strict,
        )

    def find_all(
        self,
        entity_type: EntityTypeFilter[_EntityT] = None,
        /,
        *,
        limit: int | None = None,
        attrs: Mapping[str, object] | None = None,
        **attributes: object,
    ) -> list[_EntityT]:
        """Return objects of ``entity_type`` matching the given attributes.

        Subclasses are included; pass a tuple for several types or
        ``exact(cls)`` for one class only. Filters match by equality, and a
        class or enum value also matches anything narrower; see
        ``docs/traversal.md`` for lists, regexes, presence tests, and
        callables. On multi-valued relationships a filter means membership,
        so ``find_all(AHU, feeds=vav)`` works as expected. ``attrs`` passes
        filters whose names collide with these keyword options.
        """
        from .traversal import merge_filters, select

        return select(
            self.entities, entity_type, merge_filters(attributes, attrs), limit
        )

    def find(
        self,
        entity_type: EntityTypeFilter[_EntityT] = None,
        /,
        *,
        attrs: Mapping[str, object] | None = None,
        **attributes: object,
    ) -> _EntityT | None:
        """Return the first matching object, or ``None``."""
        from .traversal import merge_filters, select

        found = select(self.entities, entity_type, merge_filters(attributes, attrs), 1)
        return found[0] if found else None

    # -- RDF output -------------------------------------------------------

    def _graph_unresolved(self) -> rdflib.Graph:
        """Build the rdflib Graph for the current model state.

        Emits, per entity: the ``rdf:type`` triple, ``rdfs:label``/
        ``rdfs:comment``, and one triple per property value. Both directions
        of an inverse pair are emitted when both are populated (inverse
        maintenance keeps them in sync in memory); this is redundant but
        valid, and keeps the serializer trivial.
        """
        g = rdflib.Graph()
        imports = set(self.imports)
        ontology_versions: dict[str, str] = {}
        for entity in self.entities:
            subject = URIRef(entity._iri)
            info = entity._classinfo_effective()
            ontology = info.ontology
            dependency = ontology.iri or ontology.source
            if dependency:
                imports.add(dependency)
            if ontology.iri and ontology.version:
                ontology_versions[ontology.iri] = ontology.version
            for base in type(entity).__mro__:
                base_info = base.__dict__.get("_classinfo")
                if base_info is not None and base_info.ontology.iri:
                    imports.add(base_info.ontology.iri)
                    if base_info.ontology.version:
                        ontology_versions[base_info.ontology.iri] = (
                            base_info.ontology.version
                        )
            g.add((subject, RDF.type, URIRef(info.iri)))
            g.add((subject, RDFS.label, Literal(entity.label)))
            if entity.comment is not None:
                g.add((subject, RDFS.comment, Literal(entity.comment)))
            for spec, value in entity._property_values():
                dependency = getattr(value, "ontology_iri", None)
                if dependency:
                    imports.add(dependency)
                    vocabulary = getattr(value, "_registry", None)
                    if vocabulary is not None and vocabulary.ontology.version:
                        ontology_versions[dependency] = vocabulary.ontology.version
                if spec.kind == "class":
                    obj = URIRef(value.meta.iri)
                elif spec.kind == "object":
                    obj = URIRef(value.iri if hasattr(value, "iri") else value._iri)
                elif spec.kind in {"enum", "term"}:
                    obj = URIRef(value.iri)
                elif spec.kind == "value":
                    if hasattr(value, "_iri"):
                        obj = URIRef(value._iri)
                    elif hasattr(value, "iri"):
                        obj = URIRef(value.iri)
                    else:
                        obj = Literal(value)
                else:
                    obj = Literal(value)
                g.add((subject, URIRef(spec.predicate), obj))
        ontology_subject = URIRef(self.ontology_iri)
        g.add((ontology_subject, RDF.type, OWL.Ontology))
        if self.name is not None:
            g.add((ontology_subject, RDFS.label, Literal(self.name)))
        for dependency in sorted(imports):
            if dependency != self.ontology_iri:
                g.add((ontology_subject, OWL.imports, URIRef(dependency)))
                if version := ontology_versions.get(dependency):
                    g.add((URIRef(dependency), OWL.versionInfo, Literal(version)))
        _bind_prefixes(g, {"": self.namespace, **self.prefixes})
        return g

    def export_ontology(self, destination: str | Path | None = None) -> rdflib.Graph:
        """Return the portable schema graph for generated configurations in this model.

        The extension ontology graph is stored with the generated registry and
        includes class identities, parent links, and imports. When ``destination``
        is supplied it is serialized as Turtle and the graph is also returned.
        """
        graph = rdflib.Graph()
        registries = set(self._loaded_registries) | {
            entity.meta.registry
            for entity in self.entities
            if not entity.meta.registry._schema_covers_dependencies
            and entity.meta.registry.schema_graph is not None
        }
        for registry in registries:
            if registry._schema_covers_dependencies:
                continue
            schema = registry.schema_graph
            if schema is not None:
                for triple in schema:
                    graph.add(triple)
        if destination is not None:
            graph.serialize(destination=str(destination), format="turtle")
        return graph

    def check(self) -> ResolutionReport:
        """Check domain constraints without materializing a snapshot."""
        from .lifecycle import check_model

        return check_model(self)

    def resolve(self) -> ResolvedModel:
        """Resolve all deferred intentions into a cached frozen snapshot."""
        if (
            self._resolved_cache is not None
            and self._resolved_cache.source_revision == self._revision
        ):
            return self._resolved_cache
        from .lifecycle import resolve_model

        snapshot = resolve_model(self)
        self._resolved_cache = snapshot
        return snapshot

    def _cached_plan[T](self, key: tuple[Any, ...], create: Callable[[], T]) -> T:
        """Reuse domain plans with a bounded cache of authored input fingerprints."""
        if key not in self._plan_cache:
            result = create()
            if len(self._plan_cache) >= 256:
                self._plan_cache.pop(next(iter(self._plan_cache)))
            self._plan_cache[key] = result
        return self._plan_cache[key]

    def compile(
        self,
        *,
        validate: bool = True,
        shapes: object = None,
        infer: bool = True,
    ) -> ResolvedModel:
        """Resolve and, by default, validate one concrete immutable graph.

        Validation uses the exact SHACL graph bundled with each generated
        package when available. Pass ``validate=False`` only for deliberate
        diagnostic or partial-model workflows.
        """
        snapshot = self.resolve()
        if validate:
            report = self.validate(shapes, infer=infer)
            if not report:
                from .errors import ValidationError

                raise ValidationError(
                    f"compiled model does not conform:\n{report}",
                    report=report,
                )
        return snapshot

    def graph(self) -> rdflib.Graph:
        """Resolve the authored model and return its concrete RDF graph."""
        if self._loaded_graph is not None:
            graph = rdflib.Graph()
            for prefix, namespace in self._loaded_graph.namespaces():
                graph.bind(prefix, namespace, replace=True)
            graph += self._loaded_graph
            return graph
        return self.resolve().graph()

    def save(self, path: str | Path, *, format: str | None = None) -> None:
        """Serialize to a file; format inferred from the extension
        (``.ttl``, ``.nt``, ``.xml``, ``.jsonld``) unless given."""
        path = Path(path)
        if format is None:
            format = {
                ".ttl": "turtle",
                ".nt": "nt",
                ".xml": "xml",
                ".rdf": "xml",
                ".jsonld": "json-ld",
            }.get(path.suffix, "turtle")
        self.graph().serialize(destination=str(path), format=format)

    # -- validation -------------------------------------------------------

    def validate(
        self, shapes: object = None, *, infer: bool = True
    ) -> ValidationReport:
        """Validate against SHACL shapes (via shifty).

        ``shapes`` may be an rdflib Graph, a path, or a URL; when omitted,
        the shapes graphs advertised by the generated packages used in this
        model are collected automatically (each package knows its ontology
        source). Violations are mapped back to entities where possible.
        """
        from .validation import validate_model

        return validate_model(self, shapes, infer=infer)

    def __repr__(self) -> str:
        return f"<Model {self.namespace} ({len(self.entities)} entities)>"


_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def _snake(class_name: str) -> str:
    """Class name -> auto-name prefix (``AHU`` -> ``ahu``,
    ``Air_Handling_Unit`` -> ``air_handling_unit``)."""
    return _CAMEL_BOUNDARY.sub("_", class_name).lower()


class _SystemScope:
    """Deferred ``with model.system(...)`` member collector."""

    def __init__(self, model: Model, name: str, *, label: str | None) -> None:
        self.model = model
        self.name = name
        self.label = label
        self._start = 0
        self.entity: Entity | None = None
        self._boundaries: list[Any] = []
        self._transaction: Any = None

    def __enter__(self) -> _SystemScope:
        self._transaction = self.model._atomic()
        self._transaction.__enter__()
        self._start = len(self.model.entities)
        return self

    def boundary(self, *points: Entity | PortHandle | PointRef) -> _SystemScope:
        """Mark boundary points; staged until the scope closes, direct after."""
        if self.entity is not None:
            self.entity.boundary(*points)
        else:
            self._boundaries.extend(points)
        return self

    def __exit__(self, *exc_info: object) -> None:
        if exc_info[0] is not None:
            self._transaction.__exit__(*exc_info)
            return
        try:
            self._finish()
        except BaseException:
            import sys

            self._transaction.__exit__(*sys.exc_info())
            raise
        self._transaction.__exit__(None, None, None)

    def _finish(self) -> None:
        candidates = self.model.entities[self._start :]
        if not candidates:
            raise ModelingError(f"system {self.name!r} has no members")
        from .lifecycle import domain_for

        domain = domain_for(self.model)
        if domain is None:
            raise TypeError("system scope requires a connection domain")
        self.entity = domain.create_system(
            self.model, self.name, self.label, candidates
        )
        self.entity.boundary(*self._boundaries)


#: Conventional prefixes for namespaces whose final path segment is not the
#: name people use for them.
_WELL_KNOWN_PREFIXES = {
    "http://data.ashrae.org/standard223#": "s223",
}

_PREFIX_CHARS = re.compile(r"[^A-Za-z0-9_-]")


def _bind_prefixes(graph: rdflib.Graph, declared: Mapping[str, str]) -> None:
    """Bind one stable prefix per namespace used in ``graph``.

    ``declared`` bindings win. Other namespaces take a conventional prefix or
    one derived from their final path segment (``.../watr#`` -> ``watr``), in
    sorted namespace order, so output prefixes depend only on the IRIs used
    and never on the order entities were created.
    """
    graph.bind("owl", OWL, replace=True)
    taken = {prefix for prefix, _ns in graph.namespaces()} | set(declared)
    bound = {str(ns) for _prefix, ns in graph.namespaces()} | set(declared.values())
    # Vocabulary terms appear as predicates and objects; subjects are model
    # instances or ontology IRIs, which read better written out in full.
    used: set[str] = set()
    for _subject, predicate, obj in graph:
        if predicate == OWL.imports:
            continue
        for term in (predicate, obj):
            if isinstance(term, URIRef):
                ns = _split_namespace(str(term))
                if ns is not None:
                    used.add(ns)
    for prefix, ns in declared.items():
        graph.bind(prefix, ns, replace=True)
    for ns in sorted(used - bound):
        stem = _WELL_KNOWN_PREFIXES.get(ns) or _namespace_stem(ns)
        prefix, index = stem, 2
        while prefix in taken:
            prefix = f"{stem}{index}"
            index += 1
        taken.add(prefix)
        graph.bind(prefix, ns, replace=True)


def _namespace_stem(namespace: str) -> str:
    """Prefix candidate from a namespace's final non-empty path segment."""
    segment = namespace.rstrip("#/").rsplit("/", 1)[-1]
    stem = _PREFIX_CHARS.sub("", segment).lower().strip("-")
    if not stem or not stem[0].isalpha():
        return "ns"
    return stem


def _split_namespace(class_iri: str) -> str | None:
    """Namespace part of a class IRI (up to and including '#' or last '/')."""
    for sep in ("#", "/"):
        if sep in class_iri:
            return class_iri.rsplit(sep, 1)[0] + sep
    return None


def _copy_collections(value: Any) -> Any:
    """Copy mutable containers while preserving entity and vocabulary identity."""
    if isinstance(value, list):
        return [_copy_collections(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_copy_collections(item) for item in value)
    if isinstance(value, dict):
        return {key: _copy_collections(item) for key, item in value.items()}
    if isinstance(value, set):
        return set(value)
    return value
