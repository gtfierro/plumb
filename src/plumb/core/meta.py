"""Ontology metadata carried by generated classes.

Every class the compiler emits carries a :class:`ClassInfo` (as the
``_classinfo`` class attribute) describing where it came from: its IRI, label,
definition, defining ontology, and the SHACL-derived property specs it
declares. The ``.meta`` accessor on entities (see ``entity.py``) presents this
information read-only; the docstring generator in ``plumb.gen`` renders
the same data, so hover-docs and runtime introspection can never disagree.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal
from collections.abc import Iterable
from pathlib import Path

if TYPE_CHECKING:
    import rdflib
    from .containment import ContainmentTable
    from .entity import Entity
    from .enums import EnumValue
    from .lifecycle import Domain


@dataclass(frozen=True)
class OntologyInfo:
    """Identity of the ontology a class or property was generated from."""

    name: str
    """Short human name, e.g. ``"Brick"``."""

    iri: str
    """The ontology's IRI (the ``owl:Ontology`` subject)."""

    version: str | None = None
    """``owl:versionInfo`` at generation time, if declared."""

    source: str | None = None
    """Where the ontology was loaded from (URL or file path)."""


@dataclass(frozen=True)
class PropertySpec:
    """One generated attribute: an ontology property scoped to a class.

    Specs are declared by the class that introduces the attribute and are
    inherited by subclasses through the normal Python MRO. A subclass that
    narrows a constraint (e.g. a SHACL qualified shape raising ``minCount``)
    re-declares a spec with the same ``name``, shadowing the parent's.
    """

    name: str
    """Python attribute name (snake_cased label / local name)."""

    predicate: str
    """IRI of the RDF property this attribute serializes to."""

    kind: Literal["object", "class", "literal", "enum", "term", "value"]
    """Entity link, punned class term, literal, enum/term, or RDF value."""

    label: str | None = None
    """``rdfs:label`` of the property."""

    definition: str | None = None
    """``skos:definition`` / ``rdfs:comment`` text for the property."""

    ranges: tuple[str, ...] = ()
    """Python class names of allowed entity or punned class targets.

    Stored as names, not types, so generated modules can reference classes
    defined later in the file; resolved lazily through the :class:`Registry`.
    An empty tuple means unconstrained.
    """

    range_groups: tuple[tuple[str, ...], ...] = ()
    """Conjunction of alternative class IRIs, authoritative for range checks.

    ``ranges`` is the Python annotation projection; Python has no general
    intersection type. An empty group list uses ``ranges`` for handwritten specs.
    """

    sources: tuple[str, ...] = ()
    """Source declarations and shapes contributing to the effective constraint."""

    datatype: type | None = None
    """Python type of the value (literal properties only)."""

    required: bool = False
    """Whether the constructor enforces a minimum (cyclic requirements defer)."""

    min_count: int = 0
    """Semantic SHACL minimum, including requirements deferred by constructors."""

    max_count: int | None = None
    """SHACL ``maxCount``; ``None`` means unbounded. ``1`` means scalar."""

    inverse: str | None = None
    """Python attribute name of the inverse property (``owl:inverseOf``),
    used to keep both directions of an edge in sync in memory."""

    enum_ranges: tuple[str, ...] = ()
    """Allowed enum roots as *IRIs* (enum properties only): a value must be
    one of these members or a descendant in the enumeration hierarchy."""

    term_ranges: tuple[str, ...] = ()
    """Allowed RDF class IRIs for compiled vocabulary individuals."""

    deferred: bool = False
    """True when the value may name a deferred endpoint (a port, declared
    point, or connection handle) that resolution replaces with the concrete
    connection point or connection, e.g. a sensor's observation location."""


@dataclass(frozen=True)
class CPSlot:
    """A connection-point requirement from a 223-style qualified shape.

    "A Chiller must have >= 1 OutletConnectionPoint whose medium is
    Fluid-Water" becomes ``CPSlot(cp_class='OutletConnectionPoint',
    direction='out', medium='...#Fluid-Water', min_count=1)``. The
    connection negotiator materializes these on demand.
    """

    cp_class: str
    """Python class name of the connection point (Inlet/Outlet/...)."""

    direction: Literal["in", "out", "bi"]
    """Flow direction implied by the connection-point class."""

    medium: str | None
    """Required medium as an enum IRI, or None when unconstrained."""

    medium_options: tuple[str, ...] = ()
    """Alternative allowed medium roots projected from ``sh:or``."""

    min_count: int = 1
    """``sh:qualifiedMinCount``."""

    max_count: int | None = None
    """``sh:qualifiedMaxCount``; ``None`` means unbounded."""

    name: str | None = None
    label: str | None = None


@dataclass(frozen=True)
class CPConstraint:
    """A recursive constructive subset of a SHACL shape.

    Boolean nodes retain SHACL's ``and``, ``or``, and ``xone`` structure;
    leaf nodes carry a :class:`CPSlot`. The connection negotiator can use this
    tree to select a complete valid layout without flattening alternatives.
    """

    operator: Literal["slot", "and", "or", "xone", "opaque"]
    """``opaque`` preserves a validation-only boolean branch."""
    slot: CPSlot | None = None
    children: tuple[CPConstraint, ...] = ()


@dataclass(frozen=True)
class PortSlot:
    """One unconditional connection-point requirement, resolved for inspection.

    ``medium`` and ``medium_options`` are allowed hierarchy roots, not
    necessarily exact media. Unregistered enum IRIs remain strings.
    """

    point_class: type[Entity]
    direction: Literal["in", "out", "bi"]
    medium: EnumValue | str | None
    medium_options: tuple[EnumValue | str, ...]
    min_count: int
    max_count: int | None
    name: str | None = None
    label: str | None = None


@dataclass(frozen=True)
class PortContract:
    """Inherited requirements for points a solver may place on an entity.

    ``slots`` are unconditional requirements. ``constraints`` preserve
    ``and``/``or``/``xone`` alternatives from compiled SHACL shapes. Neither
    structure assigns names to points that have not been authored or resolved.
    """

    slots: tuple[PortSlot, ...]
    constraints: tuple[CPConstraint, ...]

    def describe(self) -> str:
        """Summarize directions, counts, media, and nested shape constraints."""

        def short_name(value: EnumValue | str) -> str:
            iri = value if isinstance(value, str) else value.iri
            return iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]

        def line(
            direction: str,
            point_class: str,
            minimum: int,
            maximum: int | None,
            medium: EnumValue | str | None,
            medium_options: tuple[EnumValue | str, ...],
        ) -> str:
            count = f"{minimum}..{maximum if maximum is not None else 'any'}"
            allowed = medium_options or ((medium,) if medium is not None else ())
            media = (
                f"; medium roots: {', '.join(short_name(item) for item in allowed)}"
                if allowed
                else ""
            )
            return f'direction="{direction}" -> {point_class} (count {count}){media}'

        def constraint_lines(node: CPConstraint, indent: str) -> list[str]:
            if node.operator == "slot" and node.slot is not None:
                slot = node.slot
                return [
                    f"{indent}- "
                    + line(
                        slot.direction,
                        short_name(slot.cp_class),
                        slot.min_count,
                        slot.max_count,
                        slot.medium,
                        slot.medium_options,
                    )
                ]
            if node.operator == "opaque":
                return [f"{indent}- validation-only constraint"]
            heading = {"and": "all of", "or": "any of", "xone": "exactly one of"}
            lines = [f"{indent}- {heading[node.operator]}:"]
            for child in node.children:
                lines.extend(constraint_lines(child, indent + "  "))
            return lines

        if not self.slots and not self.constraints:
            return "No port requirements declared."

        lines: list[str] = []
        if self.slots:
            lines.append("Unconditional ports:")
            for slot in self.slots:
                lines.append(
                    "  - "
                    + (f"{slot.name}: " if slot.name else "")
                    + line(
                        slot.direction,
                        slot.point_class.__name__,
                        slot.min_count,
                        slot.max_count,
                        slot.medium,
                        slot.medium_options,
                    )
                )
        if self.constraints:
            lines.append("Shape constraints:")
            for node in self.constraints:
                lines.extend(constraint_lines(node, "  "))
        return "\n".join(lines)


class Registry:
    """Per-generated-package index of classes and UX negotiation tables.

    Each generated package creates exactly one ``Registry``; every class in
    the package registers itself here (via ``Entity.__init_subclass__``) so
    property ranges — stored as strings in :class:`PropertySpec` — can be
    resolved to real classes at runtime without import-order gymnastics.
    """

    def __init__(self, ontology: OntologyInfo) -> None:
        self.ontology = ontology
        self.by_name: dict[str, type[Entity]] = {}
        self.by_iri: dict[str, type[Entity]] = {}
        self.enums_by_iri: dict[str, EnumValue] = {}
        self.terms_by_iri: dict[str, object] = {}
        self._dependencies: tuple[Registry, ...] = ()
        self._domain: Domain | None = None
        self.schema_graph = None
        self._schema_covers_dependencies = False
        #: QUDT quantity kind IRI -> Sensor subclass name, for ``.sensor()``
        self.sensor_classes: dict[str, str] = {}
        # Imported lazily to avoid a module cycle (containment needs Entity).
        from .containment import ContainmentTable

        self.containment: ContainmentTable = ContainmentTable(self)

    @property
    def schema_graph(self) -> rdflib.Graph | None:
        """The package's bundled schema, parsed once when it is needed."""
        if self._schema_graph is None and self._schema_path is not None:
            from rdflib import Graph

            self._schema_graph = Graph().parse(self._schema_path)
        return self._schema_graph

    @schema_graph.setter
    def schema_graph(self, graph: rdflib.Graph | None) -> None:
        self._schema_graph = graph
        self._schema_path: Path | None = None

    def register(self, cls: type[Entity]) -> None:
        """Record a generated class. Called automatically at class creation."""
        info = cls.__dict__.get("_classinfo")
        if info is None:  # pragma: no cover - guarded by __init_subclass__
            raise TypeError(f"{cls.__name__} has no _classinfo")
        if info.canonical is not None and (
            not issubclass(cls, info.canonical)
            or info.iri != info.canonical.meta.iri
            or info.canonical.meta.canonical is not info.canonical
        ):
            raise ValueError(f"invalid canonical class for view {info.iri}")
        if info.iri in self.by_iri:
            _select_class(self.by_iri[info.iri], cls)
        info.cls = cls
        self.by_name[cls.__name__] = cls
        self.by_iri[info.iri] = cls

    def include(self, dependency: Registry) -> None:
        """Include a dependency's symbols and policy without changing its classes."""
        # Validate shared identities before updating indexes. Reuse class
        # objects; dependency classes must remain unchanged.
        combined = dict(self.by_iri)
        for iri, cls in dependency.by_iri.items():
            combined[iri] = (
                _select_class(combined[iri], cls) if iri in combined else cls
            )
        for iri, value in dependency.enums_by_iri.items():
            if iri in self.enums_by_iri and self.enums_by_iri[iri] is not value:
                raise ValueError(f"incompatible imported enum identity {iri}")
        if (
            self._domain is not None
            and dependency._domain is not None
            and self._domain is not dependency._domain
        ):
            raise ValueError("incompatible imported domain capabilities")
        self.by_name.update(dependency.by_name)
        self.by_iri = combined
        self.enums_by_iri.update(dependency.enums_by_iri)
        self.terms_by_iri.update(dependency.terms_by_iri)
        self._domain = self._domain or dependency._domain
        self.containment.rules.extend(
            rule
            for rule in dependency.containment.rules
            if rule not in self.containment.rules
        )
        self.sensor_classes.update(dependency.sensor_classes)
        if dependency not in self._dependencies:
            self._dependencies += (dependency,)

    @classmethod
    def compose(cls, registries: Iterable[Registry]) -> Registry:
        """Select compatible symbols and policy, dependencies before extensions."""
        # Apply dependencies before extensions; sort roots to remove input-order
        # dependence from policy selection.
        ordered: list[Registry] = []
        visited: set[Registry] = set()

        def visit(registry: Registry) -> None:
            if registry in visited:
                return
            visited.add(registry)
            for dependency in registry._dependencies:
                visit(dependency)
            ordered.append(registry)

        for registry in sorted(set(registries), key=lambda item: item.ontology.iri):
            visit(registry)
        if len(ordered) == 1:
            return ordered[0]
        combined = cls(OntologyInfo("Selected schemas", ""))
        for registry in ordered:
            combined.include(registry)
        return combined

    @classmethod
    def for_entities(
        cls, entities: Iterable[Entity], *, values: Iterable[object] = ()
    ) -> Registry:
        """Select schema context from entities and their vocabulary references."""
        registries = []
        references = list(values)
        for entity in entities:
            registries.append(entity.meta.registry)
            references.extend(value for _spec, value in entity._property_values())
        for value in references:
            registry = getattr(value, "_registry", None)
            if isinstance(registry, Registry):
                registries.append(registry)
        return cls.compose(registries)

    def resolve(self, name: str) -> type[Entity]:
        """Look up a class by its Python name (used for range checking)."""
        try:
            return self.by_name[name]
        except KeyError:
            raise KeyError(
                f"class {name!r} is not registered in the {self.ontology.name} package"
            ) from None

    @property
    def classes(self) -> tuple[type[Entity], ...]:
        """All currently registered classes, sorted by Python name."""
        return tuple(self.by_name[name] for name in sorted(self.by_name))

    def subclasses(
        self, base: type[Entity], *, recursive: bool = False
    ) -> tuple[type[Entity], ...]:
        """Registered subclasses of ``base``, directly or at any depth."""
        if recursive:
            return tuple(
                cls for cls in self.classes if cls is not base and cls.meta.is_a(base)
            )
        return tuple(cls for cls in self.classes if base in cls.meta.parents)

    def tree(self, base: type[Entity], *, max_depth: int | None = None) -> str:
        """Render the registered subclass tree rooted at ``base``.

        ``max_depth=0`` shows only the root. With multiple inheritance, a
        class appears beneath each of its direct parents.
        """
        if max_depth is not None and max_depth < 0:
            raise ValueError("max_depth must be non-negative")
        children: dict[type, list[type[Entity]]] = {}
        for cls in self.classes:
            for parent in cls.meta.parents:
                children.setdefault(parent, []).append(cls)

        lines = [base.__name__]

        def visit(parent: type[Entity], prefix: str, depth: int) -> None:
            if max_depth is not None and depth >= max_depth:
                return
            siblings = children.get(parent, ())
            for index, child in enumerate(siblings):
                last = index == len(siblings) - 1
                lines.append(f"{prefix}{'└── ' if last else '├── '}{child.__name__}")
                if child not in active:
                    active.add(child)
                    visit(child, prefix + ("    " if last else "│   "), depth + 1)
                    active.remove(child)

        active = {base}
        visit(base, "", 0)
        return "\n".join(lines)

    def register_enums(self, module: object) -> None:
        """Index every EnumValue constant in a generated enums module."""
        from .enums import EnumValue

        for value in vars(module).values():
            if isinstance(value, EnumValue):
                if value._registry is None:
                    value._registry = self
                self.enums_by_iri[value.iri] = value

    def resolve_enum(self, iri: str) -> EnumValue:
        """Look an enum member up by IRI."""
        try:
            return self.enums_by_iri[iri]
        except KeyError:
            raise KeyError(
                f"enum {iri!r} is not registered in the {self.ontology.name} package"
            ) from None


@dataclass
class ClassInfo:
    """Ontology provenance for one generated class.

    Mutable only in that ``cls`` is back-filled when the class object is
    created; everything else is fixed at generation time.
    """

    iri: str
    ontology: OntologyInfo
    registry: Registry
    label: str | None = None
    definition: str | None = None
    parent_iris: tuple[str, ...] | None = None
    """Direct RDF parents. ``None`` uses Python bases for handwritten classes."""

    ancestor_iris: tuple[str, ...] = ()
    """Transitive RDF ancestry retained even when Python bases need MRO repair."""
    properties: tuple[PropertySpec, ...] = ()
    """Specs *introduced or narrowed* by this class (not inherited ones)."""

    abstract: bool = False
    """True for organizational classes that should not be instantiated."""

    cp_slots: tuple[CPSlot, ...] = ()
    """Connection-point requirements (223-style ontologies only)."""

    cp_constraints: tuple[CPConstraint, ...] = ()
    """Boolean connection layouts projected from nested SHACL shapes."""

    class_defaults: tuple[tuple[str, str], ...] = ()
    """(property name, class name) pairs the shapes imply for every instance;
    the class is added unless the author supplies it or a subclass."""

    cls: type[Entity] | None = field(default=None, repr=False)
    """The Python class this info describes (set at registration)."""

    canonical: type[Entity] | None = None
    """Canonical dependency class when this is a package-specific typed view."""


def _select_class(first: type[Entity], second: type[Entity]) -> type[Entity]:
    """Select a compatible projection, independently of package import order."""
    # Shared IRIs require a common canonical class and comparable views.
    # Reject sibling views rather than choosing one by import order.
    if first is second:
        return first
    if first.meta.canonical is second.meta.canonical:
        if issubclass(first, second):
            return first
        if issubclass(second, first):
            return second
        raise ValueError(f"incompatible imported views of {first.meta.iri}")
    raise ValueError(f"incompatible imported class identity {first.meta.iri}")


def _port_requirements(
    cls: type[Entity],
) -> tuple[tuple[CPSlot, ...], tuple[CPConstraint, ...]]:
    """Aggregate compiled declarations once; identical conjuncts are idempotent."""
    cached = cls.__dict__.get("_port_requirements_cache")
    if cached is None:
        slots: dict[CPSlot, None] = {}
        constraints: dict[CPConstraint, None] = {}
        for base in cls.__mro__:
            info = base.__dict__.get("_classinfo")
            if info is not None:
                slots.update(dict.fromkeys(info.cp_slots))
                constraints.update(dict.fromkeys(info.cp_constraints))
        cached = tuple(slots), tuple(constraints)
        setattr(cls, "_port_requirements_cache", cached)
    return cached
