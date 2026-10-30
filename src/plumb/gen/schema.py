"""Schema extraction: ontology graph -> intermediate representation (IR).

The IR is deliberately plain (dataclasses of strings) so the emitter is a
dumb renderer and this module holds all the RDF interpretation. Sources of
information, in increasing precedence:

1. class hierarchy: ``owl:Class``/``rdfs:Class`` + ``rdfs:subClassOf``;
2. property attachment: ``rdfs:domain``/``rdfs:range`` (and
   ``schema:domainIncludes``/``rangeIncludes``) on object/datatype
   properties, falling back to SHACL node shapes that target the subjects
   (``sh:targetSubjectsOf``) or objects (``sh:targetObjectsOf``) of a
   property and constrain them with ``sh:class`` or an ``sh:or`` of them;
3. SHACL: node shapes that are (or target) a class contribute per-class
   property constraints — ``sh:class``/``sh:datatype`` ranges,
   ``minCount`` (required), ``maxCount`` (scalar vs collection).

Docstrings come from ``skos:definition`` falling back to ``rdfs:comment``;
labels from ``rdfs:label``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

import rdflib
from rdflib import OWL, RDF, RDFS, SKOS, XSD, URIRef
from rdflib.collection import Collection
from rdflib.namespace import SH

from . import naming

_SCHEMA_DOMAIN = (
    URIRef("https://schema.org/domainIncludes"),
    URIRef("http://schema.org/domainIncludes"),
)
_SCHEMA_RANGE = (
    URIRef("https://schema.org/rangeIncludes"),
    URIRef("http://schema.org/rangeIncludes"),
)

_S223 = rdflib.Namespace("http://data.ashrae.org/standard223#")

_UNCONSTRAINED_VALUE_PREDICATES = {
    "http://data.ashrae.org/standard223#hasValue",
}

#: Vocabulary namespaces whose classes we never generate.
_EXCLUDED_NS = (
    str(RDF),
    str(RDFS),
    str(OWL),
    str(SH),
    str(SKOS),
    str(XSD),
    "http://purl.org/dc/",
    "http://spinrdf.org/",
    "http://www.w3.org/2004/02/skos/",
)

#: XSD datatype -> Python type name for literal properties.
_DATATYPES: dict[URIRef, str] = {
    XSD.string: "str",
    XSD.normalizedString: "str",
    XSD.anyURI: "str",
    XSD.float: "float",
    XSD.double: "float",
    XSD.decimal: "float",
    XSD.integer: "int",
    XSD.int: "int",
    XSD.long: "int",
    XSD.nonNegativeInteger: "int",
    XSD.positiveInteger: "int",
    XSD.boolean: "bool",
}


@dataclass
class PropIR:
    """One attribute on one class, ready to emit."""

    name: str
    predicate: str
    kind: str  # "object" | "class" | "literal" | "enum" | "term" | "value"
    label: str | None = None
    definition: str | None = None
    ranges: tuple[str, ...] = ()  # python class names (object props)
    datatype: str = "str"  # python type name (literal props)
    required: bool = False
    max_count: int | None = None
    inverse: str | None = None
    enum_ranges: tuple[str, ...] = ()  # enum member IRIs (enum props)
    deferred: bool = False  # value may be a deferred port or connection


@dataclass
class CPSlotIR:
    """A connection-point requirement (223 qualified shape)."""

    cp_class: str  # python class name
    direction: str  # "in" | "out" | "bi"
    medium: str | None  # enum IRI
    medium_options: tuple[str, ...] = ()  # sh:or alternatives
    min_count: int = 1
    max_count: int | None = None


@dataclass
class CPConstraintIR:
    """A constructive projection of a SHACL connection-point expression."""

    operator: Literal["slot", "and", "or", "xone", "opaque"]
    slot: CPSlotIR | None = None
    children: list[CPConstraintIR] = field(default_factory=list)


@dataclass
class ClassIR:
    """One generated class."""

    name: str
    iri: str
    label: str | None = None
    definition: str | None = None
    parents: tuple[str, ...] = ()  # python names; empty -> Entity
    parent_iris: tuple[str, ...] = ()  # RDF edges, independent of Python bases
    ancestor_iris: tuple[str, ...] = ()
    own_props: list[PropIR] = field(default_factory=list)
    cp_slots: list[CPSlotIR] = field(default_factory=list)
    cp_constraints: list[CPConstraintIR] = field(default_factory=list)
    abstract: bool = False
    # (property name, python class name): a value of that class (or a
    # subclass) the shapes require, filled in when the author gives none.
    class_defaults: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class EnumIR:
    """One enumeration member (punned class under the enum root)."""

    name: str  # python constant name (Fluid-Air -> Fluid_Air)
    iri: str
    label: str | None = None
    definition: str | None = None
    parent: str | None = None  # python name of the parent member
    parents: tuple[str, ...] = ()  # all direct parents, including the primary
    constituents: tuple[str, ...] = ()  # python names, via composedOf/ofConstituent


@dataclass
class SchemaIR:
    """Everything the emitter needs."""

    ontology_name: str
    ontology_iri: str
    version: str | None
    source: str | None
    classes: list[ClassIR]  # topologically ordered, parents first
    enums: list[EnumIR] = field(default_factory=list)  # parents first

    def class_names(self) -> set[str]:
        return {c.name for c in self.classes}


def extract(
    graph: rdflib.Graph,
    *,
    name: str,
    source: str | None = None,
    enum_root: str | None = None,
    ontology_iri: str | None = None,
    primary_namespace: str | None = None,
    class_properties: tuple[str, ...] = (),
    deferred_properties: tuple[str, ...] = (),
) -> SchemaIR:
    """Build the IR from an ontology graph (with its imports merged in).

    ``enum_root`` (e.g. ``s223:EnumerationKind``) carves that subtree out of
    the class hierarchy: its members become EnumValue constants instead of
    entity classes.
    """
    ontology_iri, version = _ontology_identity(graph, ontology_iri)

    class_iris = _collect_class_iris(graph)
    enum_iris = _collect_enum_iris(graph, enum_root)
    class_iris -= enum_iris
    names = naming.disambiguate(
        {iri: naming.class_name(iri) for iri in class_iris},
        preferred_namespace=primary_namespace,
        deprecated={iri for iri in class_iris if _is_deprecated(graph, iri)},
    )

    classes: dict[str, ClassIR] = {}
    for iri in class_iris:
        classes[iri] = ClassIR(
            name=names[iri],
            iri=iri,
            label=_text(graph, URIRef(iri), RDFS.label),
            definition=_definition(graph, URIRef(iri)),
            parents=tuple(
                sorted(
                    names[str(parent)]
                    for parent in graph.objects(URIRef(iri), RDFS.subClassOf)
                    if str(parent) in classes or str(parent) in class_iris
                )
            ),
            parent_iris=tuple(
                sorted(
                    str(parent)
                    for parent in graph.objects(URIRef(iri), RDFS.subClassOf)
                    if isinstance(parent, URIRef)
                )
            ),
            ancestor_iris=tuple(
                sorted(
                    str(parent)
                    for parent in graph.transitive_objects(URIRef(iri), RDFS.subClassOf)
                    if isinstance(parent, URIRef) and str(parent) != iri
                )
            ),
            abstract=_is_abstract(graph, iri),
        )

    primary_ns = primary_namespace or _primary_namespace(classes)
    canonical = _canonical_predicates(graph, primary_ns)

    _attach_domain_properties(graph, classes, names, canonical)
    _attach_shape_properties(graph, classes, names, canonical, enum_iris)
    for cls in classes.values():
        for prop in cls.own_props:
            if prop.predicate in class_properties:
                prop.kind = "class"
            if prop.predicate in deferred_properties and prop.kind == "object":
                prop.deferred = True
    _attach_class_defaults(graph, classes, names, canonical, class_properties)
    _type_untyped_enum_properties(classes)

    ordered = _topo_sort(list(classes.values()))
    _resolve_mro(ordered)
    _demote_cyclic_required(ordered)
    return SchemaIR(
        ontology_name=name,
        ontology_iri=ontology_iri or "",
        version=version,
        source=source,
        classes=ordered,
        enums=_enum_ir(
            graph,
            enum_iris,
            enum_root,
            preferred_namespace=primary_namespace,
        ),
    )


def _ontology_identity(
    graph: rdflib.Graph, preferred: str | None = None
) -> tuple[str | None, str | None]:
    subjects = sorted(
        subject
        for subject in graph.subjects(RDF.type, OWL.Ontology)
        if isinstance(subject, URIRef)
    )
    if preferred is not None:
        requested = URIRef(preferred)
        return preferred, _text(graph, requested, OWL.versionInfo)
    for subject in subjects:
        return str(subject), _text(graph, subject, OWL.versionInfo)
    return None, None


def _class_metaclasses(graph: rdflib.Graph) -> set[URIRef]:
    """owl:Class, rdfs:Class, and everything declared a subclass of them.

    223 types its classes with its own metaclasses (``s223:Class``,
    ``s223:AbstractClass``, themselves ``rdfs:subClassOf rdfs:Class``);
    walking the metaclass hierarchy makes those count as class declarations.
    """
    metaclasses: set[URIRef] = set()
    frontier: list[URIRef] = [OWL.Class, RDFS.Class]
    while frontier:
        node = frontier.pop()
        if node in metaclasses:
            continue
        metaclasses.add(node)
        frontier.extend(
            sub
            for sub in graph.subjects(RDFS.subClassOf, node)
            if isinstance(sub, URIRef)
        )
    return metaclasses


def _collect_class_iris(graph: rdflib.Graph) -> set[str]:
    """All named classes worth generating (external vocab excluded)."""
    iris: set[str] = set()
    for class_type in _class_metaclasses(graph):
        for subject in graph.subjects(RDF.type, class_type):
            if not isinstance(subject, URIRef):
                continue
            iri = str(subject)
            if iri.startswith(_EXCLUDED_NS):
                continue
            iris.add(iri)
    return iris


def _is_deprecated(graph: rdflib.Graph, iri: str) -> bool:
    return any(
        value.toPython() is True
        for value in graph.objects(URIRef(iri), OWL.deprecated)
        if isinstance(value, rdflib.Literal)
    )


def _is_abstract(graph: rdflib.Graph, iri: str) -> bool:
    """223 convention: typed by an ``AbstractClass`` metaclass."""
    return any(
        isinstance(t, URIRef) and naming.local_name(str(t)) == "AbstractClass"
        for t in graph.objects(URIRef(iri), RDF.type)
    )


def _collect_enum_iris(graph: rdflib.Graph, enum_root: str | None) -> set[str]:
    """The enum subtree: the root and every transitive rdfs:subClassOf."""
    if enum_root is None:
        return set()
    seen: set[str] = set()
    frontier = [URIRef(enum_root)]
    while frontier:
        node = frontier.pop()
        if str(node) in seen:
            continue
        seen.add(str(node))
        frontier.extend(
            child
            for child in graph.subjects(RDFS.subClassOf, node)
            if isinstance(child, URIRef)
        )
    return seen


def _enum_ir(
    graph: rdflib.Graph,
    enum_iris: set[str],
    enum_root: str | None,
    *,
    preferred_namespace: str | None = None,
) -> list[EnumIR]:
    """Enum members in parents-first order, with disambiguated names."""
    if not enum_iris:
        return []
    names = naming.disambiguate(
        {iri: naming.class_name(iri) for iri in enum_iris},
        preferred_namespace=preferred_namespace,
    )
    ordered: list[EnumIR] = []
    seen: set[str] = set()

    def visit(iri: str, parent: str | None) -> None:
        if iri in seen:
            return
        seen.add(iri)
        subject = URIRef(iri)
        ordered.append(
            EnumIR(
                name=names[iri],
                iri=iri,
                label=_text(graph, subject, RDFS.label),
                definition=_definition(graph, subject),
                parent=parent,
            )
        )
        for child in sorted(graph.subjects(RDFS.subClassOf, subject), key=str):
            if str(child) in enum_iris:
                visit(str(child), names[iri])

    assert enum_root is not None
    visit(enum_root, None)
    for member in ordered:
        member.parents = tuple(
            sorted(
                names[str(parent)]
                for parent in graph.objects(URIRef(member.iri), RDFS.subClassOf)
                if str(parent) in enum_iris
            )
        )
        member.constituents = tuple(
            sorted(
                {
                    names[str(constituent)]
                    for composition in graph.objects(
                        URIRef(member.iri), _S223.composedOf
                    )
                    for constituent in graph.objects(composition, _S223.ofConstituent)
                    if str(constituent) in enum_iris
                }
            )
        )
    return ordered


def _primary_namespace(classes: dict[str, ClassIR]) -> str:
    """The modal namespace of the generated classes.

    Used to pick the canonical member of an ``owl:equivalentProperty`` group
    (Brick bundles RealEstateCore; both declare e.g. ``isPointOf``, and
    models should serialize with the Brick one).
    """
    counts: dict[str, int] = {}
    for cls in classes.values():
        ns = _ns(cls.iri)
        counts[ns] = counts.get(ns, 0) + 1
    return max(sorted(counts), key=lambda ns: counts[ns]) if counts else ""


def _canonical_predicates(graph: rdflib.Graph, primary_ns: str) -> dict[str, str]:
    """predicate IRI -> canonical IRI across owl:equivalentProperty groups.

    The representative is the member in the primary namespace, else the
    sorted-first member (deterministic either way).
    """
    groups: dict[str, set[str]] = {}
    for a, b in graph.subject_objects(OWL.equivalentProperty):
        if not (isinstance(a, URIRef) and isinstance(b, URIRef)):
            continue
        merged = groups.get(str(a), {str(a)}) | groups.get(str(b), {str(b)})
        for member in merged:
            groups[member] = merged
    canonical: dict[str, str] = {}
    for member, group in groups.items():
        preferred = sorted(
            group, key=lambda iri: (not iri.startswith(primary_ns), iri)
        )[0]
        canonical[member] = preferred
    return canonical


def _attach_domain_properties(
    graph: rdflib.Graph,
    classes: dict[str, ClassIR],
    names: dict[str, str],
    canonical: dict[str, str],
) -> None:
    """Attach rdfs:domain / schema:domainIncludes declared properties."""
    inverse_names = _inverse_map(graph, canonical)
    props: set[URIRef] = set()
    for prop_type in (OWL.ObjectProperty, OWL.DatatypeProperty, RDF.Property):
        for prop in graph.subjects(RDF.type, prop_type):
            if isinstance(prop, URIRef):
                props.add(prop)
    # Sorted iteration keeps attachment deterministic when several predicates
    # map to the same Python name (e.g. brick:isPointOf vs rec:isPointOf).
    for prop in sorted(props):
        domains = _values(graph, prop, (RDFS.domain, *_SCHEMA_DOMAIN))
        domains = [d for d in domains if d in classes]
        if not domains:
            domains = [
                d
                for d in _shape_target_classes(graph, prop, SH.targetSubjectsOf)
                if d in classes
            ]
        if not domains:
            continue
        ir = _prop_ir(graph, prop, names, inverse_names, canonical)
        for domain in _drop_redundant_domains(domains, classes):
            _attach_prop(classes[domain], ir)


def _shape_target_classes(
    graph: rdflib.Graph, prop: URIRef, target: URIRef
) -> list[str]:
    """Classes required of a property's subjects or objects by SHACL.

    Reads node shapes declaring ``target`` (``sh:targetSubjectsOf`` or
    ``sh:targetObjectsOf``) ``prop`` whose focus nodes must have ``sh:class``
    C, or satisfy an ``sh:or`` whose every member is an ``sh:class``.
    """
    out: set[str] = set()
    for shape in graph.subjects(target, prop):
        out.update(_values(graph, shape, (SH["class"],)))
        for members in graph.objects(shape, SH["or"]):
            alternatives = list(Collection(graph, members))
            classes = [graph.value(alt, SH["class"]) for alt in alternatives]
            if alternatives and all(isinstance(c, URIRef) for c in classes):
                out.update(str(c) for c in classes)
    return sorted(out)


def _attach_prop(cls: ClassIR, ir: PropIR) -> None:
    """Attach a property, resolving same-name collisions by namespace.

    When two predicates yield the same attribute name on one class, the one
    sharing the class's own namespace wins (a Brick class keeps the Brick
    predicate over the bundled RealEstateCore one); otherwise first-attached
    (sorted order) stays.
    """
    existing = next((p for p in cls.own_props if p.name == ir.name), None)
    if existing is None:
        cls.own_props.append(ir)
        return
    class_ns = _ns(cls.iri)
    if _ns(ir.predicate) == class_ns and _ns(existing.predicate) != class_ns:
        cls.own_props[cls.own_props.index(existing)] = ir


def _ns(iri: str) -> str:
    """Namespace part of an IRI (through '#' or the last '/')."""
    for sep in ("#", "/"):
        if sep in iri:
            return iri.rsplit(sep, 1)[0] + sep
    return iri


def _prop_ir(
    graph: rdflib.Graph,
    prop: URIRef,
    names: dict[str, str],
    inverse_names: dict[str, str],
    canonical: dict[str, str],
) -> PropIR:
    ranges = _values(graph, prop, (RDFS.range, *_SCHEMA_RANGE))
    if not ranges:
        ranges = _shape_target_classes(graph, prop, SH.targetObjectsOf)
    datatype_ranges = [URIRef(r) for r in ranges if URIRef(r) in _DATATYPES]
    is_literal = bool(datatype_ranges) or (
        (prop, RDF.type, OWL.DatatypeProperty) in graph
    )
    predicate = canonical.get(str(prop), str(prop))
    kind = "literal" if is_literal else "object"
    if predicate in _UNCONSTRAINED_VALUE_PREDICATES:
        kind = "value"
    return PropIR(
        name=naming.property_name(predicate),
        predicate=predicate,
        kind=kind,
        label=_text(graph, prop, RDFS.label),
        definition=_definition(graph, prop),
        ranges=tuple(sorted(names[r] for r in ranges if r in names)),
        datatype=_DATATYPES.get(datatype_ranges[0], "str")
        if datatype_ranges
        else "str",
        inverse=inverse_names.get(predicate),
    )


def _attach_shape_properties(
    graph: rdflib.Graph,
    classes: dict[str, ClassIR],
    names: dict[str, str],
    canonical: dict[str, str],
    enum_iris: set[str],
) -> None:
    """Fold SHACL node-shape constraints into per-class properties.

    A shape applies to a class when the shape *is* the class (223 style) or
    when it ``sh:targetClass``-es it. Constraints on an already-attached
    property narrow it (required/max_count/ranges); unknown paths declare a
    new attribute on that class. Qualified shapes over connection points
    become :class:`CPSlotIR` entries for the negotiator rather than
    attributes.
    """
    inverse_names = _inverse_map(graph, canonical)
    by_name = {item.name: item for item in classes.values()}
    pairs = list(_shape_class_pairs(graph, classes))
    pairs.sort(
        key=lambda pair: (
            _class_depth(classes[pair[1]], by_name),
            pair[1],
            str(pair[0]),
        )
    )
    for shape, class_iri in pairs:
        for referenced in graph.objects(shape, SH.node):
            classes[class_iri].cp_constraints.append(
                _cp_expression(graph, referenced, names, enum_iris, set())
            )
        for operator in ("and", "or", "xone"):
            predicate = SH[operator]
            for members in graph.objects(shape, predicate):
                children = [
                    _cp_expression(graph, member, names, enum_iris, set())
                    for member in graph.items(members)
                ]
                classes[class_iri].cp_constraints.append(
                    CPConstraintIR(operator=operator, children=children)
                )
        for pshape in graph.objects(shape, SH.property):
            path = graph.value(pshape, SH.path)
            if not isinstance(path, URIRef):
                continue  # property paths beyond a plain IRI are out of scope
            # Entity owns these fields and the serializer always emits a
            # label. Treating their shapes as ontology relations would create
            # misleading generated attributes such as ``label_``—notably for
            # WaTr's metaclass shape.
            if path in {RDFS.label, RDFS.comment}:
                continue

            qualified = graph.value(pshape, SH.qualifiedValueShape)
            if qualified is not None:
                slot = _cp_slot(graph, pshape, qualified, names, enum_iris)
                if slot is not None:
                    classes[class_iri].cp_slots.append(slot)
                continue  # qualified constraints are not plain attributes

            min_count = _int(graph, pshape, SH.minCount)
            max_count = _int(graph, pshape, SH.maxCount)
            sh_class = graph.value(pshape, SH["class"])
            sh_datatype = graph.value(pshape, SH.datatype)

            cls = classes[class_iri]
            predicate = canonical.get(str(path), str(path))
            prop_name = naming.property_name(predicate)
            existing = next((p for p in cls.own_props if p.name == prop_name), None)
            if existing is None:
                inherited = _inherited_prop(cls, prop_name, by_name)
                declarative = any(
                    item is not None
                    for item in (min_count, max_count, sh_class, sh_datatype)
                )
                if inherited is not None and not declarative:
                    # A SPARQL-only shape constrains an inherited property; it
                    # does not redeclare or loosen its Python descriptor.
                    continue
                if inherited is not None:
                    existing = replace(inherited)
                else:
                    kind = "literal" if sh_datatype is not None else "object"
                    if predicate in _UNCONSTRAINED_VALUE_PREDICATES:
                        kind = "value"
                    existing = PropIR(
                        name=prop_name,
                        predicate=predicate,
                        kind=kind,
                        label=_text(graph, path, RDFS.label),
                        definition=_definition(graph, path),
                        inverse=inverse_names.get(predicate),
                    )
                cls.own_props.append(existing)
            if min_count is not None and min_count >= 1:
                existing.required = True
            if max_count is not None:
                existing.max_count = max_count
            if isinstance(sh_class, URIRef) and str(sh_class) in enum_iris:
                existing.kind = "enum"
                existing.enum_ranges = tuple(
                    sorted(set(existing.enum_ranges) | {str(sh_class)})
                )
            elif isinstance(sh_class, URIRef) and str(sh_class) in names:
                existing.ranges = tuple(
                    sorted(set(existing.ranges) | {names[str(sh_class)]})
                )
            if isinstance(sh_datatype, URIRef) and sh_datatype in _DATATYPES:
                existing.kind = "literal"
                existing.datatype = _DATATYPES[sh_datatype]


def _type_untyped_enum_properties(classes: dict[str, ClassIR]) -> None:
    """Give untyped declarations of enum-valued predicates the enum kind.

    A SPARQL-only shape declares a predicate without saying what it holds
    (223 checks ``hasMedium`` compatibility on every Concept). When every
    typed declaration of that predicate is an enumeration, the untyped ones
    accept any enum value rather than defaulting to entity links.
    """
    by_predicate: dict[str, list[PropIR]] = {}
    for cls in classes.values():
        for prop in cls.own_props:
            by_predicate.setdefault(prop.predicate, []).append(prop)
    for props in by_predicate.values():
        untyped = [p for p in props if p.kind == "object" and not p.ranges]
        typed = [p for p in props if p not in untyped]
        if untyped and typed and all(p.kind == "enum" for p in typed):
            for prop in untyped:
                prop.kind = "enum"


def _attach_class_defaults(
    graph: rdflib.Graph,
    classes: dict[str, ClassIR],
    names: dict[str, str],
    canonical: dict[str, str],
    class_properties: tuple[str, ...],
) -> None:
    """Record class-implied values of punned-class properties.

    A shape requiring at least one ``sh:qualifiedValueShape [sh:class X]``
    value on a class-valued property (WaTr: a SedimentationTank performs
    Process-Settling) determines that value for every instance. The runtime
    adds ``X`` unless the author supplies ``X`` or a subclass, which is what
    WaTr's ``ClassDefaultsRule`` infers in RDF.
    """
    if not class_properties:
        return
    for shape, class_iri in _shape_class_pairs(graph, classes):
        for pshape in graph.objects(shape, SH.property):
            path = graph.value(pshape, SH.path)
            qualified = graph.value(pshape, SH.qualifiedValueShape)
            if not isinstance(path, URIRef) or qualified is None:
                continue
            predicate = canonical.get(str(path), str(path))
            minimum = _int(graph, pshape, SH.qualifiedMinCount)
            value = graph.value(qualified, SH["class"])
            if (
                predicate in class_properties
                and minimum is not None
                and minimum >= 1
                and str(value) in names
            ):
                entry = (naming.property_name(predicate), names[str(value)])
                if entry not in classes[class_iri].class_defaults:
                    classes[class_iri].class_defaults.append(entry)
    for cls in classes.values():
        cls.class_defaults.sort()


def _inherited_prop(
    cls: ClassIR,
    name: str,
    by_name: dict[str, ClassIR],
) -> PropIR | None:
    """Find the nearest property declaration in ``cls``'s parent graph."""
    for parent_name in cls.parents:
        parent = by_name.get(parent_name)
        if parent is None:
            continue
        own = next((prop for prop in parent.own_props if prop.name == name), None)
        if own is not None:
            return own
        inherited = _inherited_prop(parent, name, by_name)
        if inherited is not None:
            return inherited
    return None


def _class_depth(
    cls: ClassIR,
    by_name: dict[str, ClassIR],
    seen: frozenset[str] = frozenset(),
) -> int:
    """Maximum parent depth, used to apply base-class shapes first."""
    if cls.name in seen:
        return 0
    parents = [by_name[name] for name in cls.parents if name in by_name]
    if not parents:
        return 0
    nested_seen = seen | {cls.name}
    return 1 + max(_class_depth(parent, by_name, nested_seen) for parent in parents)


_CP_DIRECTIONS = {
    "InletConnectionPoint": "in",
    "OutletConnectionPoint": "out",
    "BidirectionalConnectionPoint": "bi",
}


def _cp_slot(
    graph: rdflib.Graph,
    pshape,
    qualified,
    names: dict[str, str],
    enum_iris: set[str],
) -> CPSlotIR | None:
    """Interpret a qualified shape as a connection-point requirement.

    Only qualified shapes whose value class is a known connection-point
    class are meaningful to the negotiator; others are ignored (they still
    apply at validation time).
    """
    value_class = graph.value(qualified, SH["class"])
    if not isinstance(value_class, URIRef) or str(value_class) not in names:
        return None
    cp_name = names[str(value_class)]
    direction = _CP_DIRECTIONS.get(cp_name)
    if direction is None:
        return None
    # The qualified shape itself, or a node shape it references, may
    # constrain the medium. WaTr uses the direct form while S223 commonly
    # wraps the properties in sh:node.
    media: set[str] = set()
    medium_shapes = [qualified, *graph.objects(qualified, SH.node)]
    for medium_shape in medium_shapes:
        for nested in graph.objects(medium_shape, SH.property):
            nested_path = graph.value(nested, SH.path)
            nested_class = graph.value(nested, SH["class"])
            if (
                isinstance(nested_path, URIRef)
                and naming.local_name(str(nested_path)) == "hasMedium"
                and isinstance(nested_class, URIRef)
                and str(nested_class) in enum_iris
            ):
                media.add(str(nested_class))
            if (
                isinstance(nested_path, URIRef)
                and naming.local_name(str(nested_path)) == "hasMedium"
            ):
                for alternatives in graph.objects(nested, SH["or"]):
                    for alternative in graph.items(alternatives):
                        option = graph.value(alternative, SH["class"])
                        if isinstance(option, URIRef) and str(option) in enum_iris:
                            media.add(str(option))
    # SHACL has no minimum when qualifiedMinCount is absent: a shape with only
    # qualifiedMaxCount 0 forbids such points rather than requiring one.
    min_count = _int(graph, pshape, SH.qualifiedMinCount) or 0
    max_count = _int(graph, pshape, SH.qualifiedMaxCount)
    return CPSlotIR(
        cp_class=cp_name,
        direction=direction,
        medium=next(iter(media)) if len(media) == 1 else None,
        medium_options=tuple(sorted(media)) if len(media) > 1 else (),
        min_count=min_count,
        max_count=max_count,
    )


def _cp_expression(
    graph: rdflib.Graph,
    shape,
    names: dict[str, str],
    enum_iris: set[str],
    active: set[rdflib.term.Node],
) -> CPConstraintIR:
    """Project a nested SHACL shape into constructive CP constraints.

    Constraints unrelated to connection points remain validation-only. A
    recursive ``sh:node`` reference is ignored here rather than recursively
    expanding forever; the original SHACL graph remains authoritative during
    validation.
    """
    if shape in active:
        return CPConstraintIR(operator="opaque")
    active = active | {shape}
    conjuncts: list[CPConstraintIR] = []

    for pshape in graph.objects(shape, SH.property):
        path = graph.value(pshape, SH.path)
        qualified = graph.value(pshape, SH.qualifiedValueShape)
        if not isinstance(path, URIRef) or qualified is None:
            continue
        slot = _cp_slot(graph, pshape, qualified, names, enum_iris)
        if slot is not None:
            conjuncts.append(CPConstraintIR(operator="slot", slot=slot))

    for referenced in graph.objects(shape, SH.node):
        expression = _cp_expression(graph, referenced, names, enum_iris, active)
        conjuncts.append(expression)

    for operator in ("and", "or", "xone"):
        for members in graph.objects(shape, SH[operator]):
            children = [
                _cp_expression(graph, member, names, enum_iris, active)
                for member in graph.items(members)
            ]
            conjuncts.append(CPConstraintIR(operator=operator, children=children))

    if not conjuncts:
        # Preserve validation-only branches of or/xone. Dropping one would
        # incorrectly make the remaining constructive branches unconditional.
        return CPConstraintIR(operator="opaque")
    if len(conjuncts) == 1:
        return conjuncts[0]
    return CPConstraintIR(operator="and", children=conjuncts)


def _shape_class_pairs(graph: rdflib.Graph, classes: dict[str, ClassIR]):
    """Yield (shape node, class IRI) for every shape that governs a class."""
    seen: set[tuple[rdflib.term.Node, str]] = set()

    def emit(shape: rdflib.term.Node, class_iri: str):
        pair = (shape, class_iri)
        if pair not in seen:
            seen.add(pair)
            return pair
        return None

    for shape in graph.subjects(RDF.type, SH.NodeShape):
        if isinstance(shape, URIRef) and str(shape) in classes:
            if (pair := emit(shape, str(shape))) is not None:
                yield pair
        for target in graph.objects(shape, SH.targetClass):
            if str(target) in classes:
                if (pair := emit(shape, str(target))) is not None:
                    yield pair

    # WaTr also attaches SHACL predicates directly to a class without always
    # asserting sh:NodeShape. These are still constructive class constraints.
    shape_predicates = (SH.property, SH.node, SH["and"], SH["or"], SH.xone)
    for class_iri in sorted(classes):
        shape = URIRef(class_iri)
        if any(
            graph.value(shape, predicate) is not None for predicate in shape_predicates
        ):
            if (pair := emit(shape, class_iri)) is not None:
                yield pair


def _inverse_map(graph: rdflib.Graph, canonical: dict[str, str]) -> dict[str, str]:
    """canonical predicate IRI -> python name of its inverse partner.

    Recognizes ``owl:inverseOf`` plus ontology-local inverse predicates
    (223 declares ``s223:inverseOf`` instead of OWL's).
    """
    inverse_preds = {OWL.inverseOf} | {
        p
        for p in set(graph.predicates())
        if isinstance(p, URIRef) and naming.local_name(str(p)) == "inverseOf"
    }
    inverses: dict[str, str] = {}
    for pred in inverse_preds:
        for a, b in graph.subject_objects(pred):
            if isinstance(a, URIRef) and isinstance(b, URIRef):
                ca = canonical.get(str(a), str(a))
                cb = canonical.get(str(b), str(b))
                inverses[ca] = naming.property_name(cb)
                inverses[cb] = naming.property_name(ca)
    return inverses


def _drop_redundant_domains(
    domains: list[str], classes: dict[str, ClassIR]
) -> list[str]:
    """Remove domains that are subclasses of another listed domain (the
    property is inherited through Python anyway)."""
    ancestors: dict[str, set[str]] = {}

    def collect(iri: str) -> set[str]:
        if iri in ancestors:
            return ancestors[iri]
        result: set[str] = set()
        by_name = {c.name: c.iri for c in classes.values()}
        for parent_name in classes[iri].parents:
            parent_iri = by_name.get(parent_name)
            if parent_iri:
                result.add(parent_iri)
                result |= collect(parent_iri)
        ancestors[iri] = result
        return result

    kept = []
    domain_set = set(domains)
    for domain in domains:
        if collect(domain) & domain_set:
            continue
        kept.append(domain)
    return kept


def _topo_sort(classes: list[ClassIR]) -> list[ClassIR]:
    """Parents before children; stable (alphabetical) within a level."""
    by_name = {c.name: c for c in classes}
    ordered: list[ClassIR] = []
    seen: set[str] = set()
    visiting: set[str] = set()

    def visit(cls: ClassIR) -> None:
        if cls.name in seen:
            return
        if cls.name in visiting:
            # subclass cycle in the ontology: break it by treating the
            # remaining parent link as already emitted (documented limitation)
            return
        visiting.add(cls.name)
        for parent in cls.parents:
            if parent in by_name:
                visit(by_name[parent])
        visiting.discard(cls.name)
        seen.add(cls.name)
        ordered.append(cls)

    for cls in sorted(classes, key=lambda c: c.name):
        visit(cls)
    return ordered


def _resolve_mro(ordered: list[ClassIR]) -> None:
    """Make every class's parent list Python-inheritable, in emit order.

    RDF allows parent combinations Python's C3 linearization rejects. We
    simulate the class creation with dummy types and repair each parent
    tuple in place:

    1. drop parents that are ancestors of another parent (redundant in
       Python: inherited anyway);
    2. order the rest most-derived-first (a C3 requirement);
    3. if linearization still fails, drop trailing parents until it works
       (the remaining links stay recorded in ``meta``/RDF via the class IRI,
       just not in the Python MRO — see DESIGN.md "known hard problems").
    """
    dummies: dict[str, type] = {}
    root = type("_Root", (), {})

    for cls in ordered:
        bases: list[type] = []
        for parent in cls.parents:
            dummy = dummies.get(parent)
            if dummy is not None and dummy not in bases:
                bases.append(dummy)
        # 1. remove redundant ancestors
        bases = [
            b
            for b in bases
            if not any(other is not b and issubclass(other, b) for other in bases)
        ]
        # 2. most-derived-first, stable otherwise
        bases.sort(key=lambda b: sum(issubclass(b, o) for o in bases), reverse=True)
        # 3. degrade until C3 accepts
        while True:
            try:
                dummy = type(cls.name, tuple(bases) or (root,), {})
                break
            except TypeError:
                bases.pop()
        dummies[cls.name] = dummy
        cls.parents = tuple(b.__name__ for b in bases)


def _demote_cyclic_required(ordered: list[ClassIR]) -> None:
    """Break constructor deadlocks between mutually-required object props.

    223 example: a Junction requires >= 1 ConnectionPoint, and every
    ConnectionPoint requires its Connectable — neither can be constructed
    first if both requirements are constructor-enforced. When required
    object property P on class C targets a range R that itself requires a
    back-link to C (or an ancestor of C), P is demoted to validate-time
    (optional constructor arg): the "pointed-at" side keeps its requirement
    because its target naturally exists first.
    """
    by_name = {c.name: c for c in ordered}

    def ancestors(cls: ClassIR) -> set[str]:
        out: set[str] = set()
        frontier = list(cls.parents)
        while frontier:
            parent = frontier.pop()
            if parent in out or parent not in by_name:
                continue
            out.add(parent)
            frontier.extend(by_name[parent].parents)
        return out

    def effective_required_object_props(cls: ClassIR) -> list[PropIR]:
        merged: dict[str, PropIR] = {}
        for parent in cls.parents:
            if parent in by_name:
                for prop in effective_required_object_props(by_name[parent]):
                    merged[prop.name] = prop
        for prop in cls.own_props:
            if prop.kind == "object" and prop.required:
                merged[prop.name] = prop
        return list(merged.values())

    def effective_ranges(cls: ClassIR, prop_name: str) -> set[str]:
        """Ranges for a property, including declarations up the hierarchy
        (a subclass row that only narrows minCount carries no sh:class)."""
        out: set[str] = set()
        frontier = [cls.name]
        seen: set[str] = set()
        while frontier:
            current = frontier.pop()
            if current in seen or current not in by_name:
                continue
            seen.add(current)
            for prop in by_name[current].own_props:
                if prop.name == prop_name:
                    out.update(prop.ranges)
            frontier.extend(by_name[current].parents)
        return out

    for cls in ordered:
        family = {cls.name} | ancestors(cls)
        for prop in cls.own_props:
            if prop.kind != "object" or not prop.required:
                continue
            for range_name in effective_ranges(cls, prop.name):
                range_cls = by_name.get(range_name)
                if range_cls is None:
                    continue
                back = effective_required_object_props(range_cls)
                if any(
                    set(other.ranges) & family
                    for other in back
                    if other.name != prop.name
                ):
                    prop.required = False
                    break


def _values(graph, subject, predicates) -> list[str]:
    out: list[str] = []
    for predicate in predicates:
        for value in graph.objects(subject, predicate):
            if isinstance(value, URIRef):
                out.append(str(value))
    return out


def _text(graph, subject, predicate) -> str | None:
    value = graph.value(subject, predicate)
    return str(value) if value is not None else None


def _int(graph, subject, predicate) -> int | None:
    value = graph.value(subject, predicate)
    return int(value) if value is not None else None


def _definition(graph, subject) -> str | None:
    return _text(graph, subject, SKOS.definition) or _text(graph, subject, RDFS.comment)
