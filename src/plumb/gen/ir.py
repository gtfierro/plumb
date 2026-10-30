"""Compiler representation shared by normalization, domain adapters, and emission."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class PropIR:
    """One attribute on one class, ready to emit."""

    name: str
    predicate: str
    kind: str  # "object" | "class" | "literal" | "enum" | "term" | "value"
    label: str | None = None
    definition: str | None = None
    ranges: tuple[str, ...] = ()  # python class names (object props)
    range_groups: tuple[tuple[str, ...], ...] = ()  # conjunction of IRI unions
    sources: tuple[str, ...] = ()  # contributing property shapes/declarations
    datatype: str = "str"  # python type name (literal props)
    required: bool = False
    min_count: int = 0  # graph requirement; survives constructor deferral
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
    source: str | None = None
    reason: str | None = None


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
    effective_props: dict[str, PropIR] = field(default_factory=dict, repr=False)
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
    connection_support: list[dict[str, object]] = field(default_factory=list)

    def class_names(self) -> set[str]:
        return {c.name for c in self.classes}
