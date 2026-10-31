"""HVAC: generated from RDF/SHACL. DO NOT EDIT."""
# ruff: noqa
from __future__ import annotations
from dataclasses import dataclass as _dataclass
from typing import Iterable as _Iterable
import plumb.s223 as _BASE
from plumb.core import (Entity as _Entity, ClassInfo as _ClassInfo, CPSlot as _CPSlot,
    Model as _Model, Registry as _Registry, OntologyInfo as _OntologyInfo,
    PropertySpec as _PropertySpec, TermOne as _TermOne, Lit as _Lit, Rel as _Rel, RelOne as _RelOne, EnumOne as _EnumOne, EnumSet as _EnumSet, ValueOne as _ValueOne,
    PropertySchema as _PropertySchema, QuantityDefinition as _QuantityDefinition,
    QuantityAmount as _QuantityAmount, TermValue as _TermValue, EnumValue as _EnumValue, DeferredEndpoint as _DeferredEndpoint)
from plumb.core.points import PointDeclaration as _PointDeclaration, PointRef as _PointRef, PointGroupRef as _PointGroupRef
from plumb.core.shape_constraints import ShapeValues as _ShapeValues
from plumb.qudt import units as _units, quantity_kinds as _kinds
ONTOLOGY = _OntologyInfo('HVAC', 'https://watermetadata.org/plumb/hvac#', source='ontology/hvac.ttl')
_REGISTRY = _Registry(ONTOLOGY)
REGISTRY = _REGISTRY
_REGISTRY.include(_BASE.REGISTRY)
from pathlib import Path as _Path
from rdflib import Graph as _Graph
if '__file__' in globals():
    _REGISTRY.schema_graph = _Graph().parse(_Path(__file__).with_name('_shapes.ttl'))
_REGISTRY.terms_by_iri.update({})

class AirWaterCoolingCoil(_BASE.CoolingCoil):
    'A cooling coil with separate air and water inlets and outlets.'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/hvac#AirWaterCoolingCoil',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Air and water cooling coil',
        definition='A cooling coil with separate air and water inlets and outlets.',
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Air', min_count=1, max_count=1, name='air_inlet', label='air_inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Air', min_count=1, max_count=1, name='air_outlet', label='air_outlet'), _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='water_inlet', label='water_inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='water_outlet', label='water_outlet'),),
    )
    _shape_max_ports = 4
    air_inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Air'), direction='in', label='air_inlet')
    air_outlet = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Air'), direction='out', label='air_outlet')
    water_inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='water_inlet')
    water_outlet = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='water_outlet')
    _point_declarations = {
        'air_inlet': air_inlet,
        'air_outlet': air_outlet,
        'water_inlet': water_inlet,
        'water_outlet': water_outlet,
    }
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_BASE.ActuatableProperty] | None = None,
        cnx: _Iterable[_BASE.ConnectionPoint] | None = None,
        connected: _Iterable[_BASE.Connectable] | None = None,
        connected_from: _Iterable[_BASE.Connectable] | None = None,
        connected_through: _Iterable[_BASE.Connection] | None = None,
        connected_to: _Iterable[_BASE.Connectable] | None = None,
        contains_: _Iterable[_BASE.Equipment | _BASE.Junction] | None = None,
        executes: _Iterable[_BASE.Function] | None = None,
        has_connection_point: _Iterable[_BASE.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_BASE.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_BASE.PhysicalSpace] | None = None,
        has_property: _Iterable[_BASE.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        medium: _Iterable[_EnumValue] | None = None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'actuated_by_property': actuated_by_property,
            'cnx': cnx,
            'connected': connected,
            'connected_from': connected_from,
            'connected_through': connected_through,
            'connected_to': connected_to,
            'contains_': contains_,
            'executes': executes,
            'has_connection_point': has_connection_point,
            'has_optional_connection_point': has_optional_connection_point,
            'has_physical_location': has_physical_location,
            'has_property': has_property,
            'has_role': has_role,
            'medium': medium,
        })

__all__ = ['ONTOLOGY', 'REGISTRY', 'AirWaterCoolingCoil']
