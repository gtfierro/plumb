"""Compile reusable SHACL property groups and ontology extension classes.

The optional codegen annotations select Python projections and the installed
base package. Domain facts always come from RDF classes and SHACL constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from importlib import import_module
from keyword import iskeyword
from math import isfinite
from typing import Any

import rdflib
from rdflib import OWL, RDF, RDFS, SKOS, URIRef
from rdflib.namespace import SH

from plumb.core import Entity, PropertySpec, Registry

from . import naming
from .constraints import cardinality, property_shapes

CODEGEN = rdflib.Namespace("https://watermetadata.org/plumb/codegen#")
S223 = rdflib.Namespace("http://data.ashrae.org/standard223#")
QUDT = rdflib.Namespace("http://qudt.org/schema/qudt/")


@dataclass
class ValuesIR:
    name: str
    source: str
    required: list[rdflib.term.Node] = dataclass_field(default_factory=list)
    defaults: list[rdflib.term.Node] = dataclass_field(default_factory=list)
    choices: list[rdflib.term.Node] = dataclass_field(default_factory=list)
    minimum: int = 0
    maximum: int | None = None


@dataclass
class PointIR:
    name: str
    source: str
    direction: str
    medium: str
    label: str | None
    count: int


@dataclass
class ConfigurationIR:
    iri: str
    name: str
    base: type[Entity]
    parent_name: str
    specs: dict[str, PropertySpec]
    new_specs: list[PropertySpec]
    values: list[ValuesIR]
    points: list[PointIR]
    maximum_ports: int | None
    inherited_values: list[ValuesIR] = dataclass_field(default_factory=list)


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
    base_registry: Registry,
    known: dict[str, ConfigurationIR],
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
        inherited_values = [*inherited.inherited_values, *inherited.values]
    else:
        if parent not in base_registry.by_iri:
            raise ValueError(f"{iri}: unlinked parent {parent}")
        base = base_registry.by_iri[parent]
        specs = dict(base._effective_specs())
        parent_name = f"_BASE.{base.__name__}"
        inherited_values = []
    new_specs = []
    by_predicate = {spec.predicate: spec for spec in specs.values()}
    nodes = [iri, *sorted(graph.subjects(SH.targetClass, iri), key=str)]
    grouped: dict[str, list[rdflib.term.Node]] = {}
    for node in nodes:
        for path, props in _fields(graph, node).items():
            grouped.setdefault(path, []).extend(props)
    points = []
    constraints = []
    maximum_ports = None
    for path, props in sorted(grouped.items()):
        if path == str(S223.hasConnectionPoint):
            for prop in props:
                qualified = graph.value(prop, SH.qualifiedValueShape)
                if qualified is None:
                    maximum = graph.value(prop, SH.maxCount)
                    if maximum is not None:
                        maximum_ports = int(str(maximum))
                    continue
                cp_class = graph.value(qualified, SH["class"])
                direction = {
                    str(S223.InletConnectionPoint): "in",
                    str(S223.OutletConnectionPoint): "out",
                    str(S223.BidirectionalConnectionPoint): "bi",
                }.get(str(cp_class))
                fields = _fields(graph, qualified)
                medium = _value(graph, fields.get(str(S223.hasMedium), []), SH.hasValue)
                label = _value(graph, fields.get(str(RDFS.label), []), SH.hasValue)
                count = graph.value(prop, SH.qualifiedMinCount)
                maximum = graph.value(prop, SH.qualifiedMaxCount)
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
                points.append(
                    PointIR(
                        _name(graph, prop, "port"),
                        str(prop),
                        direction,
                        str(medium),
                        str(label) if label is not None else None,
                        int(str(count)),
                    )
                )
            continue
        if path in {str(RDFS.label), str(RDFS.comment)}:
            continue
        spec = by_predicate.get(path)
        if spec is None:
            name = naming.property_name(path)
            datatype = _value(graph, props, SH.datatype)
            maximum = _value(graph, props, SH.maxCount)
            sh_class = _value(graph, props, SH["class"])
            spec = PropertySpec(
                name=name,
                predicate=path,
                kind="literal" if datatype is not None else "term",
                datatype=float
                if datatype in {rdflib.XSD.double, rdflib.XSD.float}
                else str
                if datatype is not None
                else None,
                max_count=int(maximum) if maximum is not None else 1,
                term_ranges=(str(sh_class),) if sh_class else (),
            )
            specs[name] = spec
            new_specs.append(spec)
        required = _constants(graph, props, SH.hasValue)
        defaults = _constants(graph, props, SH.defaultValue)
        choices_node = _value(graph, props, SH["in"])
        choices = list(graph.items(choices_node)) if choices_node is not None else []
        minima = _constants(graph, props, SH.minCount)
        maxima = _constants(graph, props, SH.maxCount)
        minimum, maximum = cardinality(
            graph, props, minimum=spec.min_count, maximum=spec.max_count
        )
        if maximum is not None and (len(required) > maximum or minimum > maximum):
            raise ValueError(f"{iri}: contradictory cardinalities on {path}")
        if choices and any(value not in choices for value in [*required, *defaults]):
            raise ValueError(f"{iri}: a required/default value is outside sh:in")
        if required or defaults or choices or minima or maxima:
            constraints.append(
                ValuesIR(
                    spec.name,
                    str(props[0]),
                    required,
                    defaults,
                    choices,
                    minimum,
                    maximum,
                )
            )
    if len({point.name for point in points}) != len(points):
        raise ValueError(f"{iri}: duplicate point names")
    inherited_points = (
        {point.name: point for point in inherited.points} if inherited else {}
    )
    for point in points:
        previous = inherited_points.get(point.name)
        if previous is not None and (
            previous.direction,
            previous.medium,
            previous.label,
            previous.count,
        ) != (point.direction, point.medium, point.label, point.count):
            raise ValueError(f"{iri}: conflicting inherited port {point.name}")
        if point.name in specs or point.name in naming.RESERVED:
            raise ValueError(
                f"{iri}: port name {point.name} collides with the entity API"
            )
        inherited_points[point.name] = point
    points = list(inherited_points.values())
    inherited_maximum = inherited.maximum_ports if inherited else base._shape_max_ports
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
    for name in specs:
        effective = [
            item for item in [*inherited_values, *constraints] if item.name == name
        ]
        required = {value for item in effective for value in item.required}
        limits = [item.maximum for item in effective if item.maximum is not None]
        minimum = max([item.minimum for item in effective], default=0)
        maximum = min(limits) if limits else None
        permitted = [set(item.choices) for item in effective if item.choices]
        if maximum is not None and max(len(required), minimum) > maximum:
            raise ValueError(f"{iri}: contradictory inherited cardinalities on {name}")
        if permitted:
            choices = set.intersection(*permitted)
            defaults = next(
                (item.defaults for item in reversed(effective) if item.defaults), []
            )
            if not choices or any(
                value not in choices for value in [*required, *defaults]
            ):
                raise ValueError(f"{iri}: conflicting inherited sh:in on {name}")
    return ConfigurationIR(
        str(iri),
        _name(graph, iri, naming.class_name(str(iri))),
        base,
        parent_name,
        specs,
        new_specs,
        constraints,
        points,
        maximum_ports,
        inherited_values,
    )


def compile_configurations(
    graph: rdflib.Graph,
    *,
    name: str,
    source: str | None,
) -> dict[str, str]:
    """Compile a shape-defined extension linked to an installed base package."""
    ontologies = sorted(graph.subjects(RDF.type, OWL.Ontology), key=str)
    selected = [node for node in ontologies if graph.value(node, CODEGEN.baseModule)]
    if len(selected) != 1:
        raise ValueError(
            "configuration input needs one ontology with codegen:baseModule"
        )
    ontology = selected[0]
    module_name = str(_one(graph, ontology, CODEGEN.baseModule))
    base_module = import_module(module_name)
    registry: Registry = base_module._REGISTRY
    pending = {
        str(iri): iri
        for iri in graph.subjects(RDF.type, OWL.Class)
        if isinstance(iri, URIRef)
        and list(graph.objects(iri, RDFS.subClassOf))
        and str(iri) not in registry.by_iri
    }
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
            known[iri] = _configuration(graph, pending.pop(iri), registry, known)
    configurations = list(known.values())
    local_names = {item.iri: item.name for item in configurations}
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
        if iri in registry.by_iri:
            return f"_BASE.{registry.by_iri[iri].__name__}"
        if iri in registry.enums_by_iri:
            return f"_BASE._REGISTRY.enums_by_iri[{iri!r}]"
        if iri not in terms:
            terms[iri] = f"_term_{len(terms)}"
        return terms[iri]

    def references(nodes: list[rdflib.term.Node]) -> str:
        values = [reference(node) for node in nodes]
        return "(" + ", ".join(values) + ("," if values else "") + ")"

    body = []
    for item in configurations:
        body.extend(_emit_configuration(item, graph, reference, references))
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
            if (
                field.property_class not in registry.by_iri
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
            property_cls = registry.by_iri.get(field.property_class)
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
                property_specs = property_cls._effective_specs()
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
            sorted(str(value) for value in graph.objects(URIRef(iri), RDF.type))
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
        "from plumb.core import (Entity as _Entity, ClassInfo as _ClassInfo, CPSlot as _CPSlot,",
        "    Model as _Model, Registry as _Registry, OntologyInfo as _OntologyInfo,",
        "    PropertySpec as _PropertySpec, TermOne as _TermOne, Lit as _Lit,",
        "    PropertySchema as _PropertySchema, QuantityDefinition as _QuantityDefinition,",
        "    QuantityAmount as _QuantityAmount, TermValue as _TermValue, EnumValue as _EnumValue)",
        "from plumb.core.points import PointDeclaration as _PointDeclaration, PointRef as _PointRef, PointGroupRef as _PointGroupRef",
        "from plumb.core.shape_constraints import ShapeValues as _ShapeValues",
        "from plumb.qudt import units as _units, quantity_kinds as _kinds",
        f"ONTOLOGY = _OntologyInfo({name!r}, {str(ontology)!r}, source={source!r})",
        "_REGISTRY = _Registry(ONTOLOGY)",
        "REGISTRY = _REGISTRY",
        "_REGISTRY.by_name.update(_BASE._REGISTRY.by_name)",
        "_REGISTRY.by_iri.update(_BASE._REGISTRY.by_iri)",
        "_REGISTRY.enums_by_iri.update(_BASE._REGISTRY.enums_by_iri)",
        "_REGISTRY.terms_by_iri.update(_BASE._REGISTRY.terms_by_iri)",
        "_REGISTRY.containment.rules.extend(_BASE._REGISTRY.containment.rules)",
        "_REGISTRY.sensor_classes.update(_BASE._REGISTRY.sensor_classes)",
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
    return {"__init__.py": "\n".join(lines) + "\n"}


def _annotation(spec: PropertySpec) -> str:
    if spec.kind == "literal":
        return spec.datatype.__name__ if spec.datatype else "object"
    if spec.kind in {"term", "value"}:
        return "_TermValue" if spec.kind == "term" else "object"
    if spec.kind == "enum":
        value = "_EnumValue"
    else:
        value = " | ".join(f"_BASE.{name}" for name in spec.ranges) or "_Entity"
        if spec.kind == "class":
            value = f"type[{value}]"
    return value if spec.max_count == 1 else f"_Iterable[{value}]"


def _emit_configuration(
    item: ConfigurationIR, graph: rdflib.Graph, ref: Any, refs: Any
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
            f"    {symbol} = _PropertySpec(name={spec.name!r}, predicate={spec.predicate!r}, kind={spec.kind!r}, max_count={spec.max_count!r}, term_ranges={spec.term_ranges!r}, datatype={spec.datatype.__name__ if spec.datatype else 'None'})"
        )
        descriptor = "_Lit" if spec.kind == "literal" else "_TermOne"
        lines.append(
            f"    {spec.name}: {descriptor}[{_annotation(spec)}] = {descriptor}({symbol})"
        )
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
            cp_class = {
                "in": "InletConnectionPoint",
                "out": "OutletConnectionPoint",
                "bi": "BidirectionalConnectionPoint",
            }[point.direction]
            slots.append(
                f"_CPSlot(cp_class={cp_class!r}, direction={point.direction!r}, medium={point.medium!r}, min_count={point.count}, max_count={point.count}, name={point.name!r}, label={point.label!r})"
            )
        metadata.append("cp_slots=(" + ", ".join(slots) + ",)")
    lines.append("    _classinfo = _ClassInfo(")
    lines.extend(f"        {value}," for value in metadata)
    lines.append("    )")
    if item.values:
        lines.append("    _shape_constraints = (")
        for values in item.values:
            lines.append(
                f"        _ShapeValues({values.name!r}, {values.source!r}, required={refs(values.required)}, defaults={refs(values.defaults)}, choices={refs(values.choices)}, minimum={values.minimum}, maximum={values.maximum!r}),"
            )
        lines.append("    )")
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
        effective = [
            value
            for value in [*item.inherited_values, *item.values]
            if value.name == spec.name
        ]
        values = effective[-1] if effective else None
        satisfied = any(value.required or value.defaults for value in effective)
        scalar = spec.kind not in {"class", "object", "enum"} or spec.max_count == 1
        annotation = _annotation(spec) + (" | None" if scalar else "")
        required = spec.required or values is not None and values.minimum > 0
        default = "" if required and not satisfied else " = None"
        if not scalar:
            annotation += " | None"
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
