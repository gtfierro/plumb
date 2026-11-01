"""UX overlays: per-ontology hints the compiler cannot derive from shapes.

An overlay contributes the pieces of the authoring experience that are policy
rather than ontology fact: which property ``>>`` means for a class family,
and which property realizes "X contains Y" for each class pair. Targets are
required unless explicitly wrapped in Binding(..., required=False). Resolution
produces structured diagnostics before emission; only missing optional targets
may be omitted.

Overlays are keyed by lowercased ontology name; ``for_ontology`` also accepts
a custom overlay object for extension ontologies.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any
from collections.abc import Callable
from rdflib import Graph, URIRef

from .diagnostics import CompilationError
from .ir import ClassIR, SchemaIR


@dataclass(frozen=True)
class Binding:
    """A policy target, required by default; optional targets may be absent."""

    target: str
    required: bool = True


type Target = str | Binding

#: (container class, child class, property, edge owner: "container"|"child")
ContainmentRuleSpec = tuple[Target, Target, Target, str]


@dataclass(frozen=True)
class Overlay:
    """UX hints for one ontology."""

    rshift: Mapping[Target, Target] = field(default_factory=dict)
    """class name -> property that ``>>`` adds to (e.g. Equipment feeds)."""

    containment: tuple[ContainmentRuleSpec, ...] = ()
    """Negotiation table rows for ``with`` scopes and ``contains()``."""

    enum_root: str | None = None
    """IRI of a punned enumeration root (223 EnumerationKind): its subtree
    becomes EnumValue constants in a generated ``enums`` module instead of
    entity classes."""

    class_properties: tuple[str, ...] = ()
    """Predicates whose values are punned ontology class terms."""

    ontology_iri: str | None = None
    """Ontology node to use for package identity when an imports closure
    contains several ``owl:Ontology`` declarations."""

    primary_namespace: str | None = None
    """Namespace whose terms retain unsuffixed Python names on collisions."""

    deferred_properties: tuple[str, ...] = ()
    """Predicates whose values may be a deferred port, declared point, or
    connection handle, replaced by the concrete entity on resolution."""

    connector: bool = False
    """Install the 223-style connection-point negotiator on Connectable."""

    connection_classes: Mapping[str, Target] = field(default_factory=dict)
    """medium enum IRI (or ancestor) -> Connection subclass name, used by
    the negotiator to pick Duct/Pipe/... from the resolved medium."""

    sensor_classes: Mapping[str, Target] = field(default_factory=dict)
    """QUDT quantity kind IRI -> Sensor subclass name, used by ``.sensor()``
    to pick the most specific sensor class for an observed quantity."""


@dataclass
class ResolvedBindings:
    connector: str | None = None
    rshift: dict[str, str] = field(default_factory=dict)
    containment: list[tuple[str, str, str, str]] = field(default_factory=list)
    connection_classes: dict[str, str] = field(default_factory=dict)
    sensor_classes: dict[str, str] = field(default_factory=dict)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)


def resolve(overlay: Overlay, ir: SchemaIR, graph: Graph) -> ResolvedBindings:
    """Resolve policy targets once, failing on missing required bindings."""
    result = ResolvedBindings()
    by_name = {symbol.name: symbol for symbol in ir.classes}
    by_iri = {symbol.iri: symbol for symbol in ir.classes}
    predicates = {
        prop.predicate
        for symbol in ir.classes
        for prop in symbol.effective_props.values()
    }
    enums = {enum.iri for enum in ir.enums}

    def text(target: Target) -> str:
        return target.target if isinstance(target, Binding) else target

    def symbol(target: Target) -> ClassIR:
        ref = text(target)
        item = by_iri.get(ref) or by_name.get(ref)
        if item is None:
            raise _MissingBinding(f"class {ref!r} is not in the compiled ontology")
        return item

    def prop(owner: ClassIR, target: Target):
        ref = text(target)
        item = next(
            (
                prop
                for prop in owner.effective_props.values()
                if ref in {prop.name, prop.predicate}
            ),
            None,
        )
        if item is None:
            raise _MissingBinding(f"property {ref!r} is not defined on {owner.iri}")
        return item

    def bind[T](
        kind: str, targets: tuple[Target, ...], operation: Callable[[], T]
    ) -> T | None:
        required = all(
            not isinstance(target, Binding) or target.required for target in targets
        )
        record: dict[str, Any] = {
            "kind": kind,
            "target": [text(target) for target in targets],
            "required": required,
            "status": "resolved",
            "reason": None,
        }
        try:
            value = operation()
        except ValueError as error:
            record.update(
                status="missing"
                if isinstance(error, _MissingBinding)
                else "incompatible",
                reason=str(error),
            )
            value = None
        result.diagnostics.append(record)
        return value

    if overlay.connector:
        root = "http://data.ashrae.org/standard223#Connectable"
        result.connector = bind("connector", (root,), lambda: symbol(root).name)
    for root in (overlay.enum_root,) if overlay.enum_root else ():
        bind(
            "enumeration-root",
            (root,),
            lambda: (
                root
                if (
                    (URIRef(root), None, None) in graph
                    or (None, None, URIRef(root)) in graph
                )
                else _missing(f"enumeration root {root!r} is absent")
            ),
        )
    for predicate in (*overlay.class_properties, *overlay.deferred_properties):
        bind(
            "predicate",
            (predicate,),
            lambda predicate=predicate: (
                predicate
                if predicate in predicates
                else _missing(f"predicate {predicate!r} is missing")
            ),
        )
    for cls, relation in overlay.rshift.items():

        def rshift():
            owner = symbol(cls)
            item = prop(owner, relation)
            if item.kind != "object" or item.max_count == 1:
                raise ValueError(
                    f"{owner.iri}.{item.name}: >> requires a collection of entity links"
                )
            return owner.name, item.name

        value = bind(
            "rshift",
            (cls, relation),
            rshift,
        )
        if value is not None:
            result.rshift[value[0]] = value[1]
    for container, child, relation, edge in overlay.containment:

        def containment():
            if edge not in {"container", "child"}:
                raise ValueError(f"invalid containment edge owner {edge!r}")
            a, b = symbol(container), symbol(child)
            item = prop(a if edge == "container" else b, relation)
            if item.kind != "object":
                raise ValueError(
                    f"containment property {item.predicate} must link entities"
                )
            return a.name, b.name, item.name, edge

        value = bind("containment", (container, child, relation), containment)
        if value is not None:
            result.containment.append(value)
    for medium, cls in overlay.connection_classes.items():

        def connection():
            if medium not in enums:
                raise _MissingBinding(
                    f"connection medium {medium!r} is not in the enumeration"
                )
            item = symbol(cls)
            root = "http://data.ashrae.org/standard223#Connection"
            if root in by_iri and item.iri != root and root not in item.ancestor_iris:
                raise ValueError(f"{item.iri} is not an S223 Connection class")
            if item.abstract:
                raise ValueError(
                    f"{item.iri} is abstract and cannot materialize connections"
                )
            return item.name

        value = bind("connection-class", (medium, cls), connection)
        if value is not None:
            result.connection_classes[medium] = value
    for kind, cls in overlay.sensor_classes.items():

        def sensor():
            item = symbol(cls)
            root = "http://data.ashrae.org/standard223#Sensor"
            if root in by_iri and item.iri != root and root not in item.ancestor_iris:
                raise ValueError(f"{item.iri} is not an S223 Sensor class")
            if item.abstract:
                raise ValueError(
                    f"{item.iri} is abstract and cannot materialize sensors"
                )
            return item.name

        value = bind("sensor-class", (cls,), sensor)
        if value is not None:
            result.sensor_classes[kind] = value
    failures = [
        record
        for record in result.diagnostics
        if (record["required"] and record["status"] == "missing")
        or record["status"] == "incompatible"
    ]
    if failures:
        raise CompilationError(failures)
    return result


def _missing(message: str):
    raise _MissingBinding(message)


class _MissingBinding(ValueError):
    pass


BRICK = Overlay(
    rshift={"Equipment": "feeds"},
    containment=(
        # Brick 1.4 locations are RealEstateCore spaces (rec:Building,
        # rec:Level, rec:Room, rec:HVACZone, ...), composed via rec:hasPart.
        ("Space", "Space", "has_part", "container"),
        ("Space", "Equipment", "has_location", "child"),
        ("Architecture", "Point", "has_point", "container"),
        # Deprecated brick:Location classes keep their original rules.
        ("Location", "Location", "has_part", "container"),
        # Equipment placed in a location: the edge lives on the equipment.
        ("Location", "Equipment", "has_location", "child"),
        # Assemblies: equipment within equipment.
        ("Equipment", "Equipment", "has_part", "container"),
        # Points attach to whatever hosts them.
        ("Equipment", "Point", "has_point", "container"),
        ("Location", "Point", "has_point", "container"),
    ),
    ontology_iri="https://brickschema.org/schema/1.4/Brick",
)

_S223_NS = "http://data.ashrae.org/standard223#"
_KIND = "http://qudt.org/vocab/quantitykind/"

_S223_SENSORS = {
    f"{_KIND}AbsoluteHumidity": "HumiditySensor",
    f"{_KIND}AmountOfSubstanceConcentration": "ConcentrationSensor",
    f"{_KIND}CorrelatedColorTemperature": "CorrelatedColorTemperatureSensor",
    f"{_KIND}Duv": "DuvSensor",
    f"{_KIND}ElectricCurrent": "ElectricCurrentSensor",
    f"{_KIND}GaugePressure": "GaugePressureSensor",
    f"{_KIND}Illuminance": "IlluminanceSensor",
    f"{_KIND}MassConcentration": "ConcentrationSensor",
    f"{_KIND}MassFlowRate": "FlowSensor",
    f"{_KIND}Population": "OccupantCountSensor",
    f"{_KIND}Pressure": "PressureSensor",
    f"{_KIND}RelativeHumidity": "HumiditySensor",
    f"{_KIND}Temperature": "TemperatureSensor",
    f"{_KIND}Voltage": "VoltageSensor",
    f"{_KIND}VolumeFlowRate": "FlowSensor",
}
_S223_SENSORS = {kind: f"{_S223_NS}{name}" for kind, name in _S223_SENSORS.items()}

S223 = Overlay(
    containment=(
        # Spatial hierarchy: physical spaces nest via s223:contains. (The
        # attribute is `contains_` — the trailing underscore avoids the
        # Entity.contains() method — but the negotiated `with`/.contains()
        # UX is the intended surface anyway.)
        (
            f"{_S223_NS}PhysicalSpace",
            f"{_S223_NS}PhysicalSpace",
            f"{_S223_NS}contains",
            "container",
        ),
        # A physical space encloses the domain spaces (zones) within it.
        (
            f"{_S223_NS}PhysicalSpace",
            f"{_S223_NS}DomainSpace",
            f"{_S223_NS}encloses",
            "container",
        ),
        # Equipment placed in a space: the edge lives on the equipment.
        (
            f"{_S223_NS}PhysicalSpace",
            f"{_S223_NS}Equipment",
            f"{_S223_NS}hasPhysicalLocation",
            "child",
        ),
        # Assemblies: equipment within equipment.
        (
            f"{_S223_NS}Equipment",
            f"{_S223_NS}Equipment",
            f"{_S223_NS}contains",
            "container",
        ),
    ),
    enum_root=f"{_S223_NS}EnumerationKind",
    ontology_iri="http://data.ashrae.org/standard223/1.0/model/all",
    deferred_properties=(
        f"{_S223_NS}hasObservationLocation",
        f"{_S223_NS}hasReferenceLocation",
        f"{_S223_NS}mapsTo",
    ),
    connector=True,
    connection_classes={
        f"{_S223_NS}Fluid-Air": f"{_S223_NS}Duct",
        f"{_S223_NS}Fluid-Water": f"{_S223_NS}Pipe",
        f"{_S223_NS}Fluid-NaturalGas": f"{_S223_NS}Pipe",
        f"{_S223_NS}Fluid-Oil": f"{_S223_NS}Pipe",
    },
    sensor_classes=_S223_SENSORS,
)

_WATR_NS = "https://watermetadata.org/ontology/watr#"

WATR = Overlay(
    containment=S223.containment,
    enum_root=S223.enum_root,
    ontology_iri="https://watermetadata.org/ontology/watr",
    primary_namespace=_WATR_NS,
    class_properties=(
        f"{_WATR_NS}hasProcess",
        f"{_WATR_NS}hasTreatmentObjective",
    ),
    deferred_properties=S223.deferred_properties,
    connector=True,
    connection_classes={
        **S223.connection_classes,
        f"{_S223_NS}Mix-Fluid": f"{_S223_NS}Pipe",
    },
    # Names resolve in the WaTr package, so TemperatureSensor etc. are the
    # WaTr subclasses of the S223 sensors.
    sensor_classes={
        **_S223_SENSORS,
        **{
            f"{_KIND}{kind}": f"{_WATR_NS}{name}"
            for kind, name in {
                "AmountOfSubstanceConcentration": "ConcentrationSensor",
                "MassConcentration": "ConcentrationSensor",
                "MassFlowRate": "FlowSensor",
                "VolumeFlowRate": "FlowSensor",
                "Pressure": "PressureSensor",
                "Temperature": "TemperatureSensor",
                "Conductivity": "ConductivitySensor",
                "ElectricConductivity": "ConductivitySensor",
                "Frequency": "FrequencySensor",
                "Turbidity": "TurbidityMeter",
                "Volume": "VolumeSensor",
            }.items()
        },
    },
)

#: Built-in overlays by lowercased ontology name.
BUILTIN: dict[str, Overlay] = {"brick": BRICK, "s223": S223, "watr": WATR}


def for_ontology(name: str) -> Overlay | None:
    """The built-in overlay for an ontology name, if any."""
    return BUILTIN.get(name.lower())
