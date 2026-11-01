"""Compile reusable SHACL property groups and ontology extension classes.

The optional codegen annotations select Python projections and a compiler symbol
dependency. Domain facts come from RDF and SHACL, never live Python classes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from keyword import iskeyword
from math import isfinite
from typing import Any

import rdflib
from rdflib import OWL, RDF, RDFS, SKOS, URIRef
from rdflib.namespace import SH


from . import naming
from .constraints import (
    cardinality,
    class_groups,
    property_shapes,
    project_ranges,
    refine_property,
)
from .emit import (
    emit_descriptor,
    emit_property_spec,
    emit_shape_values,
    constant_source,
    range_annotation,
)
from .ir import ClassIR, CPSlotIR, PointIR, PropIR, SchemaIR
from .symbols import FILENAME, Symbols, export_symbols
from . import s223 as adapter
from .diagnostics import FILENAME as SUPPORT_FILE, support_report
import hashlib

CODEGEN = rdflib.Namespace("https://watermetadata.org/plumb/codegen#")
S223 = rdflib.Namespace("http://data.ashrae.org/standard223#")
QUDT = rdflib.Namespace("http://qudt.org/schema/qudt/")


@dataclass
class ConfigurationIR:
    iri: str
    name: str
    base: ClassIR
    parent_name: str
    specs: dict[str, PropIR]
    new_specs: list[PropIR]
    points: list[PointIR]
    maximum_ports: int | None


@dataclass
class QuantityIR:
    name: str
    shape: str
    kind: str
    unit: str
    datatype: str
    fixed_unit: bool
    allowed_units: tuple[str, ...]
    property_class: str
    constants: dict[str, list[rdflib.term.Node]]
    default: float | None
    minimum: float | None
    maximum: float | None
    choices: tuple[float, ...]
    label: str | None
    description: str | None
    notation: str | None
    local_name: str | None


def _one(graph: rdflib.Graph, node: rdflib.term.Node, predicate: URIRef) -> Any:
    values = sorted(set(graph.objects(node, predicate)), key=str)
    if len(values) > 1:
        raise ValueError(f"{node}: ambiguous {predicate}")
    return values[0] if values else None


def _fields(
    graph: rdflib.Graph, shape: rdflib.term.Node
) -> dict[str, list[rdflib.term.Node]]:
    result: dict[str, list[rdflib.term.Node]] = {}
    for prop in property_shapes(graph, shape, reject_disjunction=True):
        path = _one(graph, prop, SH.path)
        if not isinstance(path, URIRef):
            raise ValueError(f"{shape}: complex property paths are validation-only")
        result.setdefault(str(path), []).append(prop)
    return result


def _constants(
    graph: rdflib.Graph, props: list[rdflib.term.Node], pred: URIRef
) -> list[rdflib.term.Node]:
    return sorted(
        {value for prop in props for value in graph.objects(prop, pred)}, key=str
    )


def _value(graph: rdflib.Graph, props: list[rdflib.term.Node], pred: URIRef) -> Any:
    values = _constants(graph, props, pred)
    if len(values) > 1:
        raise ValueError(f"conflicting singleton constraint {pred}: {values}")
    return values[0] if values else None


def _name(graph: rdflib.Graph, node: rdflib.term.Node, fallback: str) -> str:
    value = graph.value(node, CODEGEN.pythonName) or graph.value(node, SH.name)
    name = str(value) if value is not None else fallback
    if not name.isidentifier() or iskeyword(name) or name.startswith("_"):
        raise ValueError(f"{node}: invalid Python name {name!r}")
    return name


def _quantity(graph: rdflib.Graph, prop: rdflib.term.Node) -> QuantityIR:
    if graph.value(prop, SH.qualifiedMinCount) != rdflib.Literal(1) or graph.value(
        prop, SH.qualifiedMaxCount
    ) != rdflib.Literal(1):
        raise ValueError(
            f"{prop}: scalar quantity fields require qualified counts of one"
        )
    shape = _one(graph, prop, SH.qualifiedValueShape)
    if not isinstance(shape, URIRef):
        raise ValueError(f"{prop}: quantity value shapes must have stable IRIs")
    fields = _fields(graph, shape)
    kind = _value(graph, fields.get(str(QUDT.hasQuantityKind), []), SH.hasValue)
    unit_props = fields.get(str(QUDT.hasUnit), [])
    fixed_unit = _value(graph, unit_props, SH.hasValue)
    unit = fixed_unit or _value(graph, unit_props, SH.defaultValue)
    cls = _one(graph, shape, SH["class"])
    if kind is None or unit is None or cls is None:
        raise ValueError(
            f"{shape}: quantity needs a class, kind, and unit/default unit"
        )
    unit_choices = _value(graph, unit_props, SH["in"])
    allowed_units = (
        tuple(str(value) for value in graph.items(unit_choices))
        if unit_choices is not None
        else ()
    )
    if allowed_units and str(unit) not in allowed_units:
        raise ValueError(f"{shape}: default unit is outside sh:in")
    values = fields.get(str(S223.hasValue), [])
    if not values:
        raise ValueError(f"{shape}: numeric hasValue shape is required")
    if _value(graph, values, SH.minCount) != rdflib.Literal(1) or _value(
        graph, values, SH.maxCount
    ) != rdflib.Literal(1):
        raise ValueError(f"{shape}: numeric value requires singleton cardinality")
    datatype = _value(graph, values, SH.datatype)
    if datatype not in {rdflib.XSD.double, rdflib.XSD.float, rdflib.XSD.decimal}:
        raise ValueError(f"{shape}: unsupported quantity datatype {datatype}")
    numeric_default = _value(graph, values, SH.defaultValue)
    required_number = _value(graph, values, SH.hasValue)
    if required_number is not None:
        numeric_default = required_number
    choices: tuple[float, ...] = ()
    choices_node = _value(graph, values, SH["in"])
    if choices_node is not None:
        choices = tuple(float(str(value)) for value in graph.items(choices_node))
    if required_number is not None:
        choices = (float(required_number),)
    minimum = _optional_float(_value(graph, values, SH.minInclusive))
    maximum = _optional_float(_value(graph, values, SH.maxInclusive))
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError(f"{shape}: contradictory numeric bounds")
    if numeric_default is not None:
        number = float(numeric_default)
        if (
            not isfinite(number)
            or (minimum is not None and number < minimum)
            or (maximum is not None and number > maximum)
            or (choices and number not in choices)
        ):
            raise ValueError(
                f"{shape}: numeric default violates the source constraints"
            )
    constants = {
        path: _constants(graph, constraints, SH.hasValue)
        for path, constraints in fields.items()
        if path
        not in {
            str(S223.hasValue),
            str(QUDT.hasUnit),
            str(QUDT.hasQuantityKind),
            str(RDFS.label),
        }
    }
    fixed_label = _value(graph, fields.get(str(RDFS.label), []), SH.hasValue)
    return QuantityIR(
        name=_name(graph, prop, naming.property_name(str(shape))),
        shape=str(shape),
        kind=str(kind),
        unit=str(unit),
        datatype=str(datatype),
        fixed_unit=fixed_unit is not None,
        property_class=str(cls),
        allowed_units=allowed_units,
        constants={path: values for path, values in constants.items() if values},
        default=float(numeric_default) if numeric_default is not None else None,
        minimum=minimum,
        maximum=maximum,
        choices=choices,
        label=(
            str(fixed_label)
            if fixed_label is not None
            else str(
                graph.value(prop, SH.description)
                or graph.value(shape, RDFS.label)
                or ""
            )
            or None
        ),
        description=str(
            graph.value(shape, SH.description) or graph.value(shape, RDFS.comment) or ""
        )
        or None,
        notation=str(graph.value(shape, SKOS.notation) or "") or None,
        local_name=str(graph.value(prop, CODEGEN.localName) or "") or None,
    )


def _optional_float(value: Any) -> float | None:
    return float(value) if value is not None else None


def _configuration(
    graph: rdflib.Graph,
    iri: URIRef,
    dependency: Symbols,
    known: dict[str, ConfigurationIR],
    local_names: dict[str, str],
    ref: Any,
) -> ConfigurationIR:
    parents = list(graph.objects(iri, RDFS.subClassOf))
    if len(parents) != 1:
        raise ValueError(f"{iri}: configuration needs one constructive parent class")
    parent = str(parents[0])
    inherited = known.get(parent)
    if inherited is not None:
        base = inherited.base
        specs = dict(inherited.specs)
        parent_name = inherited.name
    else:
        if parent not in dependency.classes:
            raise ValueError(f"{iri}: unlinked parent {parent}")
        base = dependency.classes[parent]
        specs = dict(base.effective_props)
        parent_name = ref(parent)
    original = dict(specs)
    by_predicate = {spec.predicate: spec for spec in specs.values()}
    names = {key: cls.name for key, cls in dependency.classes.items()} | local_names

    def is_a(child: str, ancestor: str) -> bool:
        pending = [URIRef(child)]
        seen = set()
        while pending:
            node = pending.pop()
            key = str(node)
            if key == ancestor:
                return True
            if key in seen:
                continue
            seen.add(key)
            symbol = dependency.classes.get(key)
            if symbol is not None and ancestor in symbol.ancestor_iris:
                return True
            enum = dependency.enums.get(key)
            if enum is not None:
                by_name = {item.name: item.iri for item in dependency.enums.values()}
                pending.extend(URIRef(by_name[name]) for name in enum.parents)
            pending.extend(
                parent
                for parent in graph.objects(node, RDFS.subClassOf)
                if isinstance(parent, URIRef)
            )
        return False

    grouped: dict[str, list[rdflib.term.Node]] = {}
    for node in [iri, *sorted(graph.subjects(SH.targetClass, iri), key=str)]:
        for path, props in _fields(graph, node).items():
            grouped.setdefault(path, []).extend(props)
    points = []
    maximum_ports = None
    for path, props in sorted(grouped.items()):
        if path == str(S223.hasConnectionPoint):
            unqualified = [
                prop
                for prop in props
                if graph.value(prop, SH.qualifiedValueShape) is None
            ]
            _, maximum_ports = cardinality(graph, unqualified)
            for prop in props:
                qualified = graph.value(prop, SH.qualifiedValueShape)
                if qualified is None:
                    continue
                cp_class = _one(graph, qualified, SH["class"])
                cp_symbol = dependency.classes.get(str(cp_class))
                direction = (
                    adapter.direction(
                        graph,
                        cp_class,
                        imported_ancestors=cp_symbol.ancestor_iris if cp_symbol else (),
                    )
                    if isinstance(cp_class, URIRef)
                    else None
                )
                fields = _fields(graph, qualified)
                medium = _value(graph, fields.get(str(S223.hasMedium), []), SH.hasValue)
                label = _value(graph, fields.get(str(RDFS.label), []), SH.hasValue)
                count = _one(graph, prop, SH.qualifiedMinCount)
                maximum = _one(graph, prop, SH.qualifiedMaxCount)
                if (
                    direction is None
                    or medium is None
                    or count is None
                    or count != maximum
                    or int(str(count)) < 1
                ):
                    raise ValueError(
                        f"{prop}: named ports need a direction, exact medium, and exact count"
                    )
                if str(cp_class) not in dependency.classes:
                    raise ValueError(f"{prop}: unlinked point class {cp_class}")
                points.append(
                    PointIR(
                        _name(graph, prop, "port"),
                        str(prop),
                        direction,
                        str(medium),
                        str(label) if label is not None else None,
                        int(str(count)),
                        dependency.classes[str(cp_class)].name,
                    )
                )
            continue
        if path in {str(RDFS.label), str(RDFS.comment)}:
            continue
        spec = by_predicate.get(path)
        if spec is None:
            name = naming.property_name(path)
            if name in specs:
                raise ValueError(f"{iri}: property name collision {name} on {path}")
            datatype = any(graph.value(prop, SH.datatype) is not None for prop in props)
            groups = {
                item
                for prop in props
                for group in class_groups(graph, prop)
                for item in group
            }
            kind = "object" if datatype or groups.intersection(names) else "term"
            spec = PropIR(
                name=name,
                predicate=path,
                kind=kind,
                max_count=1 if kind == "term" else None,
            )
        spec = refine_property(spec, graph, props)
        spec = project_ranges(spec, names, set(dependency.enums), is_a)
        specs[spec.name] = spec
    if len({point.name for point in points}) != len(points):
        raise ValueError(f"{iri}: duplicate point names")
    inherited_points = {
        point.name: point for point in (inherited.points if inherited else base.points)
    }
    for point in points:
        previous = inherited_points.get(point.name)
        if previous is not None and replace(previous, source=point.source) != point:
            raise ValueError(f"{iri}: conflicting inherited port {point.name}")
        if point.name in specs or point.name in naming.RESERVED:
            raise ValueError(
                f"{iri}: port name {point.name} collides with the entity API"
            )
        inherited_points[point.name] = point
    points = list(inherited_points.values())
    inherited_maximum = inherited.maximum_ports if inherited else base.maximum_ports
    if inherited_maximum is not None:
        maximum_ports = (
            min(maximum_ports, inherited_maximum)
            if maximum_ports is not None
            else inherited_maximum
        )
    if (
        maximum_ports is not None
        and sum(point.count for point in points) > maximum_ports
    ):
        raise ValueError(f"{iri}: named points exceed inherited maximum")
    return ConfigurationIR(
        str(iri),
        local_names[str(iri)],
        base,
        parent_name,
        specs,
        [prop for name, prop in specs.items() if original.get(name) != prop],
        points,
        maximum_ports,
    )


def compile_configurations(
    graph: rdflib.Graph,
    *,
    name: str,
    source: str | None,
) -> dict[str, str]:
    """Compile an extension against data-only dependency symbols."""
    ontologies = sorted(graph.subjects(RDF.type, OWL.Ontology), key=str)
    selected = [node for node in ontologies if graph.value(node, CODEGEN.baseModule)]
    if len(selected) != 1:
        raise ValueError(
            "configuration input needs one ontology with codegen:baseModule"
        )
    ontology = selected[0]
    module_name = str(_one(graph, ontology, CODEGEN.baseModule))
    dependency = Symbols.load(module_name)
    profiles = _imported_profiles(graph, dependency)
    imported_modules: dict[str, str] = {}

    def class_reference(iri: str) -> str:
        symbol = dependency.classes[iri]
        module = symbol.python_module
        if module is None or module == module_name:
            return f"_BASE.{symbol.name}"
        if module not in imported_modules:
            imported_modules[module] = f"_DEP{len(imported_modules)}"
        return f"{imported_modules[module]}.{symbol.name}"

    pending = {
        str(iri): iri
        for iri in graph.subjects(RDF.type, OWL.Class)
        if isinstance(iri, URIRef)
        and list(graph.objects(iri, RDFS.subClassOf))
        and str(iri) not in dependency.classes
    }
    local_names = {
        iri: _name(graph, node, naming.class_name(iri)) for iri, node in pending.items()
    }
    if len(set(local_names.values())) != len(local_names):
        raise ValueError("configuration class name collision")
    known: dict[str, ConfigurationIR] = {}
    while pending:
        ready = sorted(
            iri
            for iri, node in pending.items()
            if all(
                str(parent) not in pending
                for parent in graph.objects(node, RDFS.subClassOf)
            )
        )
        if not ready:
            raise ValueError("cyclic configuration class inheritance")
        for iri in ready:
            known[iri] = _configuration(
                graph, pending.pop(iri), dependency, known, local_names, class_reference
            )
    configurations = list(known.values())
    local_names = {item.iri: item.name for item in configurations}
    class_names = {symbol.name: iri for iri, symbol in dependency.classes.items()}
    for iri, local_name in local_names.items():
        if local_name in class_names:
            raise ValueError(
                f"{iri}: generated name collision {local_name} with dependency"
            )
        class_names[local_name] = iri
    for item in configurations:
        if item.name in naming.MODULE_RESERVED:
            raise ValueError(f"{item.iri}: generated name collision {item.name}")
    terms: dict[str, str] = {}

    def reference(node: rdflib.term.Node | str) -> str:
        if isinstance(node, rdflib.Literal):
            return repr(node.toPython())
        iri = str(node)
        if iri in local_names:
            return local_names[iri]
        # QUDT individuals remain individuals even when their IRIs are punned.
        if iri.startswith("http://qudt.org/vocab/unit/"):
            return f"_units.{naming.class_name(iri)}"
        if iri.startswith("http://qudt.org/vocab/quantitykind/"):
            return f"_kinds.{naming.class_name(iri)}"
        if iri in dependency.classes:
            return class_reference(iri)
        if iri in dependency.enums:
            return f"_BASE.REGISTRY.resolve_enum({iri!r})"
        if iri not in terms:
            terms[iri] = f"_term_{len(terms)}"
        return terms[iri]

    def references(nodes: list[rdflib.term.Node]) -> str:
        values = [reference(node) for node in nodes]
        return "(" + ", ".join(values) + ("," if values else "") + ")"

    def value_reference(node):
        if isinstance(node, rdflib.Literal):
            return constant_source(node)
        if (
            str(node) in local_names
            or str(node) in dependency.classes
            or str(node) in dependency.enums
        ):
            return constant_source(node)
        return reference(node)

    body = []
    quantity_records = []
    for item in configurations:
        body.extend(
            _emit_configuration(
                item, graph, reference, references, value_reference, class_names
            )
        )
    groups = sorted(graph.subjects(CODEGEN.projection, CODEGEN.PropertySchema), key=str)
    group_names = []
    for group in groups:
        group_name = _name(
            graph, group, naming.class_name(str(group)).removesuffix("Shape")
        )
        if group_name in {*local_names.values(), *group_names, *naming.MODULE_RESERVED}:
            raise ValueError(f"{group}: generated name collision {group_name}")
        group_names.append(group_name)
        fields = []
        for prop in property_shapes(graph, group, reject_disjunction=True):
            if graph.value(prop, SH.path) != S223.hasProperty:
                raise ValueError(
                    f"{group}: property schema fields must follow s223:hasProperty"
                )
            fields.append(_quantity(graph, prop))
        if any(field.name in {"describe", "source_shape"} for field in fields):
            raise ValueError(f"{group}: field name collides with the schema API")
        if len({field.name for field in fields}) != len(fields):
            raise ValueError(f"{group}: duplicate quantity field names")
        body.extend(
            [
                "@_dataclass(frozen=True, kw_only=True)",
                f"class {group_name}(_PropertySchema):",
                f"    {str(graph.value(group, SH.description) or graph.value(group, RDFS.label) or group_name)!r}",
                f"    source_shape = {str(group)!r}",
                "    _definitions = (",
            ]
        )
        for field in fields:
            quantity_records.append(asdict(field))
            if (
                field.property_class not in dependency.classes
                and field.property_class not in known
            ):
                raise ValueError(
                    f"{field.shape}: unlinked quantity property class {field.property_class}"
                )
            kwargs = [
                f"name={field.name!r}",
                f"source_shape={field.shape!r}",
                f"kind={reference(field.kind)}",
                f"unit={reference(field.unit)}",
                f"datatype={field.datatype!r}",
                f"fixed_unit={field.fixed_unit!r}",
                f"label={field.label!r}",
                "allowed_units=("
                + ", ".join(reference(unit) for unit in field.allowed_units)
                + ("," if field.allowed_units else "")
                + ")",
                f"description={field.description!r}",
                f"notation={field.notation!r}",
                f"local_name={field.local_name!r}",
                f"minimum={field.minimum!r}",
                f"maximum={field.maximum!r}",
                f"allowed_values={field.choices!r}",
                f"property_class={reference(field.property_class)}",
            ]
            extras = []
            property_cls = dependency.classes.get(field.property_class)
            if property_cls is None:
                config = next(
                    (
                        item
                        for item in configurations
                        if item.iri == field.property_class
                    ),
                    None,
                )
                property_specs = config.specs if config else {}
            else:
                property_specs = property_cls.effective_props
            for path, values in field.constants.items():
                if path == str(S223.ofMedium):
                    kwargs.append(f"of_medium={reference(values[0])}")
                elif path == str(S223.ofSubstance):
                    kwargs.append(f"of_substance={reference(values[0])}")
                elif path == str(S223.hasAspect):
                    kwargs.append(f"aspects={references(values)}")
                else:
                    spec = next(
                        (
                            spec
                            for spec in property_specs.values()
                            if spec.predicate == path
                        ),
                        None,
                    )
                    if spec is None:
                        raise ValueError(
                            f"{field.shape}: unknown constructor predicate {path}"
                        )
                    value = (
                        reference(values[0])
                        if spec.max_count == 1
                        else references(values)
                    )
                    extras.append(f"({spec.name!r}, {value})")
            kwargs.append(
                "properties=(" + ", ".join(extras) + ("," if extras else "") + ")"
            )
            body.append(f"        _QuantityDefinition({', '.join(kwargs)}),")
        body.append("    )")
        for field in fields:
            default = f" = {field.default!r}" if field.default is not None else ""
            body.append(f"    {field.name}: float | _QuantityAmount{default}")
            docs = f"{field.label or field.name}; {field.notation or ''}; default unit {field.unit}; source {field.shape}"
            body.append(f"    {docs!r}")
        body.append("")
    term_lines = []
    for iri, symbol in terms.items():
        types = tuple(
            sorted(
                {str(value) for value in graph.objects(URIRef(iri), RDF.type)}
                | set(dependency.term_types.get(iri, ()))
            )
        )
        term_lines.append(
            f"{symbol} = _TermValue({iri!r}, types={types!r}, ontology_iri={str(ontology)!r})"
        )
    lines = [
        f'"""{name}: generated from RDF/SHACL. DO NOT EDIT."""',
        "# ruff: noqa",
        "from __future__ import annotations",
        "from dataclasses import dataclass as _dataclass",
        "from typing import Iterable as _Iterable",
        f"import {module_name} as _BASE",
        *[f"import {module} as {alias}" for module, alias in imported_modules.items()],
        "from plumb.core import (Entity as _Entity, ClassInfo as _ClassInfo, CPSlot as _CPSlot,",
        "    Model as _Model, Registry as _Registry, OntologyInfo as _OntologyInfo,",
        "    PropertySpec as _PropertySpec, TermOne as _TermOne, Lit as _Lit, Rel as _Rel, RelOne as _RelOne, EnumOne as _EnumOne, EnumSet as _EnumSet, ValueOne as _ValueOne,",
        "    PropertySchema as _PropertySchema, QuantityDefinition as _QuantityDefinition,",
        "    QuantityAmount as _QuantityAmount, TermValue as _TermValue, EnumValue as _EnumValue, DeferredEndpoint as _DeferredEndpoint)",
        "from plumb.core.points import PointDeclaration as _PointDeclaration, PointRef as _PointRef, PointGroupRef as _PointGroupRef",
        "from plumb.core.shape_constraints import ShapeValues as _ShapeValues",
        "from plumb.qudt import units as _units, quantity_kinds as _kinds",
        f"ONTOLOGY = _OntologyInfo({name!r}, {str(ontology)!r}, source={source!r})",
        "_REGISTRY = _Registry(ONTOLOGY)",
        "REGISTRY = _REGISTRY",
        "_REGISTRY.include(_BASE.REGISTRY)",
        "from pathlib import Path as _Path",
        "from rdflib import Graph as _Graph",
        "if '__file__' in globals():",
        "    _REGISTRY.schema_graph = _Graph().parse(_Path(__file__).with_name('_shapes.ttl'))",
        *term_lines,
        "_REGISTRY.terms_by_iri.update({"
        + ", ".join(f"{iri!r}: {symbol}" for iri, symbol in terms.items())
        + "})",
        "",
        *body,
        f"__all__ = {['ONTOLOGY', 'REGISTRY', *local_names.values(), *group_names]!r}",
    ]
    symbols = dependency.imported_classes()
    for item in configurations:
        parent_iri = str(next(graph.objects(URIRef(item.iri), RDFS.subClassOf)))
        parent = symbols[parent_iri]
        symbols[item.iri] = ClassIR(
            name=item.name,
            iri=item.iri,
            label=str(graph.value(URIRef(item.iri), RDFS.label) or "") or None,
            definition=str(graph.value(URIRef(item.iri), RDFS.comment) or "") or None,
            parents=(parent.name,),
            parent_iris=(parent_iri,),
            ancestor_iris=tuple(sorted({parent_iri, *parent.ancestor_iris})),
            own_props=item.new_specs,
            effective_props=item.specs,
            cp_slots=[
                *parent.cp_slots,
                *(
                    CPSlotIR(
                        cp_class=point.cp_class,
                        direction=point.direction,
                        medium=point.medium,
                        min_count=point.count,
                        max_count=point.count,
                        name=point.name,
                        label=point.label,
                    )
                    for point in item.points
                ),
            ],
            cp_constraints=list(parent.cp_constraints),
            class_defaults=list(parent.class_defaults),
            points=item.points,
            maximum_ports=item.maximum_ports,
        )
    ir = SchemaIR(
        name,
        str(ontology),
        None,
        source,
        [symbols[item.iri] for item in configurations],
        dependencies=[
            {
                "module": module_name,
                "sha256": dependency.digest,
                "ontology": dependency.ontology,
            }
        ],
        term_types={
            iri: tuple(
                sorted(
                    {str(value) for value in graph.objects(URIRef(iri), RDF.type)}
                    | set(dependency.term_types.get(iri, ()))
                )
            )
            for iri in terms
        },
    )
    shapes = "\n".join(sorted(graph.serialize(format="nt").splitlines())) + "\n"
    return {
        "__init__.py": "\n".join(lines) + "\n",
        SUPPORT_FILE: support_report(
            graph,
            ir.classes,
            quantities=quantity_records,
            profiles=profiles,
            connections=[
                {
                    "target": item.iri,
                    "source": point.source,
                    "path": str(S223.hasConnectionPoint),
                    "support": "solver",
                    "projection": asdict(point),
                    "asserted_directly": True,
                }
                for item in configurations
                for point in item.points
            ],
        ),
        FILENAME: export_symbols(
            ir, graph_digest=hashlib.sha256(shapes.encode()).hexdigest()
        ),
    }


def _imported_profiles(graph: rdflib.Graph, dependency: Symbols) -> list[ClassIR]:
    """Separate validation profiles from the dependency's canonical symbols.

    Profiles may constrain instances but cannot redefine imported identities or
    promise constructor defaults on classes owned by another package.
    """
    profiles = []
    for iri, symbol in sorted(dependency.classes.items()):
        node = URIRef(iri)
        for parent in graph.objects(node, RDFS.subClassOf):
            if not isinstance(parent, URIRef) or str(parent) not in {
                *symbol.parent_iris,
                *symbol.ancestor_iris,
            }:
                raise ValueError(
                    f"{iri}: cannot redefine imported ancestry with {parent.n3()}; "
                    "declare a local subclass instead"
                )
        python_name = _one(graph, node, CODEGEN.pythonName)
        if python_name is not None and str(python_name) != symbol.name:
            raise ValueError(f"{iri}: cannot rename imported class {symbol.name}")
        roots = [node, *graph.subjects(SH.targetClass, node)]
        if not any(
            str(parameter).startswith(str(SH))
            for root in roots
            for parameter in graph.predicates(root)
        ):
            continue
        pending = list(roots)
        visited = set()
        while pending:
            constraint = pending.pop()
            if constraint in visited:
                continue
            visited.add(constraint)
            if graph.value(constraint, SH.defaultValue) is not None:
                raise ValueError(
                    f"{iri}: imported profile default at {constraint.n3()} "
                    "cannot change the canonical constructor; "
                    "declare a local subclass instead"
                )
            # This is a validation profile: preserve complex paths and boolean
            # constraints without trying to construct a Python projection.
            for parameter in (SH.property, SH.node, SH.qualifiedValueShape, SH["not"]):
                pending.extend(graph.objects(constraint, parameter))
            for parameter in (SH["and"], SH["or"], SH.xone):
                for members in graph.objects(constraint, parameter):
                    pending.extend(graph.items(members))
        profiles.append(symbol)
    return profiles


def _value_annotation(spec: PropIR, ref: Any, class_names: dict[str, str]) -> str:
    if spec.kind == "literal":
        return spec.datatype
    if spec.kind in {"term", "value"}:
        return "_TermValue" if spec.kind == "term" else "object"
    if spec.kind == "enum":
        return "_EnumValue"
    value = range_annotation(
        spec,
        entity_base="_Entity",
        class_names={name: ref(class_names[name]) for name in spec.ranges},
    )
    return f"type[{value}]" if spec.kind == "class" else value


def _emit_configuration(
    item: ConfigurationIR,
    graph: rdflib.Graph,
    ref: Any,
    refs: Any,
    value_ref: Any,
    class_names: dict[str, str],
) -> list[str]:
    lines = [
        f"class {item.name}({item.parent_name}):",
        f"    {str(graph.value(URIRef(item.iri), RDFS.comment) or graph.value(URIRef(item.iri), RDFS.label) or item.name)!r}",
    ]
    spec_symbols = []
    for spec in item.new_specs:
        symbol = f"_spec_{spec.name}"
        spec_symbols.append(symbol)
        lines.append(
            f"    {symbol} = " + emit_property_spec(spec).replace("\n", "\n    ")
        )
        target = _value_annotation(spec, ref, class_names)
        if spec.kind == "class":
            # emit_descriptor wraps class ranges in type[].
            target = target.removeprefix("type[").removesuffix("]")
        lines.append("    " + emit_descriptor(spec, symbol, target=target))
    label = str(graph.value(URIRef(item.iri), RDFS.label) or "") or None
    description = str(graph.value(URIRef(item.iri), RDFS.comment) or "") or None
    metadata = [
        f"iri={item.iri!r}",
        "ontology=ONTOLOGY",
        "registry=_REGISTRY",
        f"label={label!r}",
        f"definition={description!r}",
        f"properties=({', '.join(spec_symbols)}{',' if spec_symbols else ''})",
    ]
    if item.points:
        slots = []
        for point in item.points:
            cp_class = point.cp_class
            slots.append(
                f"_CPSlot(cp_class={cp_class!r}, direction={point.direction!r}, medium={point.medium!r}, min_count={point.count}, max_count={point.count}, name={point.name!r}, label={point.label!r})"
            )
        metadata.append("cp_slots=(" + ", ".join(slots) + ",)")
    lines.append("    _classinfo = _ClassInfo(")
    lines.extend(f"        {value}," for value in metadata)
    lines.append("    )")
    lines.extend(emit_shape_values(item.specs.values(), reference=value_ref))
    if item.maximum_ports is not None:
        lines.append(f"    _shape_max_ports = {item.maximum_ports}")
    if item.points:
        for point in item.points:
            annotation = "_PointRef" if point.count == 1 else "_PointGroupRef"
            label = repr(point.label)
            lines.append(
                f"    {point.name} = _PointDeclaration[{annotation}](count={point.count}, medium={ref(point.medium)}, direction={point.direction!r}, label={label})"
            )
        lines.append("    _point_declarations = {")
        lines.extend(f"        {point.name!r}: {point.name}," for point in item.points)
        lines.append("    }")
    params = []
    for spec in sorted(item.specs.values(), key=lambda spec: spec.name):
        satisfied = bool(spec.required_values or spec.default_values)
        scalar = spec.kind not in {"class", "object", "enum"} or spec.max_count == 1
        value = _value_annotation(spec, ref, class_names)
        annotation = value if scalar else f"_Iterable[{value}]"
        annotation += " | None"
        required = spec.required
        default = "" if required and not satisfied else " = None"
        params.append(f"        {spec.name}: {annotation}{default},")
    lines.extend(
        [
            "    def __init__(self, name: str | None = None, *,",
            *params,
            "        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:",
            "        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{",
            *[
                f"            {spec.name!r}: {spec.name},"
                for spec in item.specs.values()
            ],
            "        })",
            "",
        ]
    )
    return lines
