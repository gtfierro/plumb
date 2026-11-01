"""Schema extraction: ontology graph -> intermediate representation (IR).

The IR is deliberately plain (dataclasses of strings) so the emitter is a
dumb renderer and this module holds all the RDF interpretation. Sources of
conjunctive constraints:

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

from dataclasses import asdict, replace

import rdflib
from rdflib import OWL, RDF, RDFS, SKOS, XSD, URIRef
from rdflib.collection import Collection
from rdflib.namespace import SH

from . import naming, s223
from .ir import ClassIR, CPConstraintIR, EnumIR, PropIR, SchemaIR
from .constraints import (
    DATATYPES as _DATATYPES,
    class_groups,
    merge_properties,
    project_ranges,
    property_shapes,
    refine_property,
)

_SCHEMA_DOMAIN = (
    URIRef("https://schema.org/domainIncludes"),
    URIRef("http://schema.org/domainIncludes"),
)
_SCHEMA_RANGE = (
    URIRef("https://schema.org/rangeIncludes"),
    URIRef("http://schema.org/rangeIncludes"),
)

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

    ordered = _topo_sort(list(classes.values()))
    primary_ns = primary_namespace or _primary_namespace(classes)
    canonical = _canonical_predicates(graph, primary_ns)

    _attach_domain_properties(graph, classes, names, canonical)
    connection_support: list[dict[str, object]] = []
    _attach_shape_properties(
        graph, classes, names, canonical, enum_iris, connection_support
    )
    for cls in classes.values():
        for prop in cls.own_props:
            if prop.predicate in class_properties:
                prop.kind = "class"
            if prop.predicate in deferred_properties and prop.kind == "object":
                prop.deferred = True
    _attach_class_defaults(graph, classes, names, canonical, class_properties)
    _type_untyped_enum_properties(classes, enum_iris)
    _name_properties(classes, primary_ns)

    # Order matters here. Compose over the original RDF parent graph first;
    # only then choose C3-compatible Python bases. After constructor-cycle
    # deferral, materialize descriptors/ports that the chosen MRO would miss.
    # Doing repair first would make a Python implementation limit weaken the
    # ontology's constraints and make the result depend on parent ordering.
    _compose_properties(ordered, graph, enum_iris)
    _resolve_mro(ordered)
    _demote_cyclic_required(ordered)
    _complete_properties(ordered)
    constant_iris = {
        str(value)
        for cls in ordered
        for prop in cls.effective_props.values()
        for value in (
            *prop.required_values,
            *prop.default_values,
            *(prop.choices or ()),
        )
        if isinstance(value, URIRef)
    }
    return SchemaIR(
        ontology_name=name,
        ontology_iri=ontology_iri or "",
        version=version,
        source=source,
        classes=ordered,
        connection_support=connection_support,
        term_types={
            iri: tuple(
                sorted(str(value) for value in graph.objects(URIRef(iri), RDF.type))
            )
            for iri in sorted(constant_iris)
        },
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
    return (URIRef(iri), RDF.type, s223.NS.AbstractClass) in graph


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
                        URIRef(member.iri), s223.NS.composedOf
                    )
                    for constituent in graph.objects(composition, s223.NS.ofConstituent)
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
    """Attach by semantic identity; Python names are assigned afterwards."""
    existing = next((p for p in cls.own_props if p.predicate == ir.predicate), None)
    if existing is None:
        cls.own_props.append(ir)
        return
    if existing.kind != ir.kind:
        raise ValueError(
            f"{ir.predicate}: equivalent declarations disagree on value kind"
        )
    existing.range_groups = tuple(
        sorted(set(existing.range_groups) | set(ir.range_groups))
    )
    existing.sources = tuple(sorted(set(existing.sources) | set(ir.sources)))


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
        range_groups=tuple(
            sorted(
                {
                    (str(value),)
                    for value in graph.objects(prop, RDFS.range)
                    if str(value) in names
                }
                | {
                    tuple(
                        sorted(
                            r for r in _values(graph, prop, _SCHEMA_RANGE) if r in names
                        )
                    )
                }
                - {()}
            )
        )
        or tuple(
            sorted(
                {
                    group
                    for shape in graph.subjects(SH.targetObjectsOf, prop)
                    for group in class_groups(graph, shape)
                }
            )
        ),
        sources=(str(prop),),
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
    connection_support: list[dict[str, object]],
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
    pairs = sorted(_shape_class_pairs(graph, classes), key=lambda p: (p[1], str(p[0])))
    for shape, class_iri in pairs:
        for referenced in graph.objects(shape, SH.node):
            expression = s223.connection_expression(
                graph, referenced, names, enum_iris, set()
            )
            classes[class_iri].cp_constraints.append(expression)
            connection_support.append(
                {
                    "target": class_iri,
                    "source": str(referenced),
                    "projection": asdict(expression),
                    "support": "validation-only"
                    if s223.contains_opaque(expression)
                    else "solver",
                }
            )
        for operator in ("and", "or", "xone"):
            predicate = SH[operator]
            for members in graph.objects(shape, predicate):
                children = [
                    s223.connection_expression(graph, member, names, enum_iris, set())
                    for member in graph.items(members)
                ]
                expression = CPConstraintIR(operator=operator, children=children)
                classes[class_iri].cp_constraints.append(expression)
                connection_support.append(
                    {
                        "target": class_iri,
                        "source": str(shape),
                        "projection": asdict(expression),
                        "support": "validation-only"
                        if s223.contains_opaque(expression)
                        else "solver",
                    }
                )
        direct_properties = set(graph.objects(shape, SH.property))
        for pshape in property_shapes(graph, shape):
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
                slot, reason = s223.connection_slot(
                    graph, pshape, qualified, names, enum_iris
                )
                if slot is not None and pshape in direct_properties:
                    classes[class_iri].cp_slots.append(slot)
                connection_support.append(
                    {
                        "target": class_iri,
                        "source": str(pshape),
                        "path": str(path),
                        "support": "solver" if slot is not None else "validation-only",
                        "projection": asdict(slot) if slot is not None else None,
                        "reason": reason,
                        "asserted_directly": slot is not None
                        and pshape in direct_properties,
                    }
                )
                continue  # qualified constraints are not plain attributes

            cls = classes[class_iri]
            predicate = canonical.get(str(path), str(path))
            existing = next(
                (p for p in cls.own_props if p.predicate == predicate), None
            )
            if existing is None:
                existing = PropIR(
                    name=naming.property_name(predicate),
                    predicate=predicate,
                    kind="value"
                    if predicate in _UNCONSTRAINED_VALUE_PREDICATES
                    else "object",
                    label=_text(graph, path, RDFS.label),
                    definition=_definition(graph, path),
                    inverse=inverse_names.get(predicate),
                )
                cls.own_props.append(existing)
            refined = refine_property(existing, graph, [pshape])
            cls.own_props[cls.own_props.index(existing)] = refined


def _type_untyped_enum_properties(
    classes: dict[str, ClassIR], enum_iris: set[str]
) -> None:
    """Give untyped declarations of enum-valued predicates the enum kind.

    A SPARQL-only shape declares a predicate without saying what it holds
    (223 checks ``hasMedium`` compatibility on every Concept). When every
    typed declaration of that predicate is an enumeration, the untyped ones
    accept any enum value rather than defaulting to entity links.
    """
    by_predicate: dict[str, list[PropIR]] = {}
    for cls in classes.values():
        for prop in cls.own_props:
            candidates = {iri for group in prop.range_groups for iri in group}
            if prop.kind == "object" and candidates and candidates <= enum_iris:
                prop.kind = "enum"
            by_predicate.setdefault(prop.predicate, []).append(prop)
    for props in by_predicate.values():
        untyped = [
            p
            for p in props
            if p.kind == "object" and not p.ranges and not p.range_groups
        ]
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
                entry = (predicate, names[str(value)])
                if entry not in classes[class_iri].class_defaults:
                    classes[class_iri].class_defaults.append(entry)
    for cls in classes.values():
        cls.class_defaults.sort()


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
    inverse_preds = (OWL.inverseOf, s223.NS.inverseOf)
    inverses: dict[str, str] = {}
    for pred in inverse_preds:
        for a, b in graph.subject_objects(pred):
            if isinstance(a, URIRef) and isinstance(b, URIRef):
                ca = canonical.get(str(a), str(a))
                cb = canonical.get(str(b), str(b))
                inverses[ca] = cb
                inverses[cb] = ca
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
            raise ValueError(f"{cls.iri}: cyclic ontology inheritance")
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


def _name_properties(classes: dict[str, ClassIR], primary_ns: str) -> None:
    """Assign one unambiguous Python name to each semantic predicate."""
    # Allocate names globally after equivalent predicates have been merged.
    # Assigning by local spelling during attachment would conflate unrelated
    # namespace terms, or let the first class visited choose a public alias.
    predicates = {prop.predicate for cls in classes.values() for prop in cls.own_props}
    names = naming.disambiguate(
        {iri: naming.property_name(iri) for iri in predicates},
        preferred_namespace=primary_ns,
    )
    for cls in classes.values():
        # Specs attached to several domains can share an object.
        cls.own_props = [
            replace(prop, name=names[prop.predicate], inverse=names.get(prop.inverse))
            for prop in cls.own_props
        ]
        cls.class_defaults = [
            (names[predicate], value) for predicate, value in cls.class_defaults
        ]


def _compose_properties(
    ordered: list[ClassIR], graph: rdflib.Graph, enum_iris: set[str]
) -> None:
    """Compute effective constraints once, before projecting Python inheritance."""
    by_name = {cls.name: cls for cls in ordered}
    names = {cls.iri: cls.name for cls in ordered}
    ancestry: dict[str, set[str]] = {}

    def is_a(child: str, parent: str) -> bool:
        if child not in ancestry:
            ancestry[child] = {
                str(node)
                for node in graph.transitive_objects(URIRef(child), RDFS.subClassOf)
            }
        return parent in ancestry[child]

    for cls in ordered:
        effective: dict[str, PropIR] = {}
        for parent in cls.parents:
            for prop in by_name[parent].effective_props.values():
                effective[prop.name] = (
                    merge_properties(effective[prop.name], prop)
                    if prop.name in effective
                    else prop
                )
        own_names = {prop.name for prop in cls.own_props}
        for prop in cls.own_props:
            effective[prop.name] = (
                merge_properties(effective[prop.name], prop)
                if prop.name in effective
                else prop
            )
        effective = {
            name: project_ranges(prop, names, enum_iris, is_a)
            for name, prop in effective.items()
        }
        cls.effective_props = effective
        cls.own_props = [effective[name] for name in sorted(own_names)]


def _demote_cyclic_required(ordered: list[ClassIR]) -> None:
    """Defer constructor requirements that need a mutually-required object.

    Semantic minimum counts remain intact for graph validation. Only the
    constructor projection is relaxed to permit staged cyclic authoring.
    """
    by_name = {cls.name: cls for cls in ordered}
    for cls in ordered:
        family = {cls.iri, *cls.ancestor_iris}
        for prop in cls.effective_props.values():
            if prop.kind != "object" or not prop.required:
                continue
            for range_name in prop.ranges:
                target = by_name.get(range_name)
                if target is None:
                    continue
                if any(
                    other.kind == "object"
                    and other.min_count > 0
                    and other.name != prop.name
                    and any(family.intersection(group) for group in other.range_groups)
                    for other in target.effective_props.values()
                ):
                    prop.required = False
                    break


def _complete_properties(ordered: list[ClassIR]) -> None:
    """Materialize constraints Python's chosen bases would otherwise lose."""
    # Python inheritance can lose both attribute implementations and static
    # subtype relationships. Repair those separately: expand annotation ranges
    # to include legitimate RDF subtypes, then redeclare missing/refined
    # descriptors and port requirements. Runtime checks still consult the full
    # semantic groups; an annotation union is not the enforcement authority.
    by_name = {cls.name: cls for cls in ordered}
    by_iri = {cls.iri: cls for cls in ordered}
    stand_ins: dict[str, type] = {}
    for cls in ordered:
        stand_ins[cls.name] = type(
            cls.name, tuple(stand_ins[p] for p in cls.parents), {}
        )
    projections: dict[tuple[str, ...], tuple[str, ...]] = {}
    for cls in ordered:
        for prop in cls.effective_props.values():
            if prop.ranges not in projections:
                roots = list(prop.ranges)
                iris = {by_name[root].iri for root in roots}
                for candidate in ordered:
                    if iris.intersection(candidate.ancestor_iris) and not any(
                        issubclass(stand_ins[candidate.name], stand_ins[root])
                        for root in roots
                    ):
                        roots.append(candidate.name)
                projections[prop.ranges] = tuple(sorted(roots))
            prop.ranges = projections[prop.ranges]
    for cls in ordered:
        stand_in = stand_ins[cls.name]
        represented = [
            cls,
            *(
                by_name[base.__name__]
                for base in stand_in.__mro__[1:]
                if base.__name__ in by_name
            ),
        ]
        slots = [slot for item in represented for slot in item.cp_slots]
        expressions = [expr for item in represented for expr in item.cp_constraints]
        defaults = [entry for item in represented for entry in item.class_defaults]
        for iri in cls.ancestor_iris:
            ancestor = by_iri.get(iri)
            if ancestor is None:
                continue
            for slot in ancestor.cp_slots:
                if slot not in slots:
                    cls.cp_slots.append(slot)
                    slots.append(slot)
            for expression in ancestor.cp_constraints:
                if expression not in expressions:
                    cls.cp_constraints.append(expression)
                    expressions.append(expression)
            for entry in ancestor.class_defaults:
                if entry not in defaults:
                    cls.class_defaults.append(entry)
                    defaults.append(entry)
        inherited: dict[str, PropIR] = {}
        for base in reversed(stand_in.__mro__[1:]):
            parent = by_name.get(base.__name__)
            if parent is not None:
                inherited.update((prop.name, prop) for prop in parent.own_props)
        own = {}
        for name, prop in cls.effective_props.items():
            if name not in inherited or inherited[name] != replace(
                prop, sources=inherited[name].sources
            ):
                own[name] = prop
        cls.own_props = [own[name] for name in sorted(own)]


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
