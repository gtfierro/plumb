"""ASM2d: generated from RDF/SHACL. DO NOT EDIT."""
# ruff: noqa
from __future__ import annotations
from dataclasses import dataclass as _dataclass
from typing import Iterable as _Iterable
import plumb.watr as _BASE
from plumb.core import (Entity as _Entity, ClassInfo as _ClassInfo, CPSlot as _CPSlot,
    Model as _Model, Registry as _Registry, OntologyInfo as _OntologyInfo,
    PropertySpec as _PropertySpec, TermOne as _TermOne, Lit as _Lit,
    PropertySchema as _PropertySchema, QuantityDefinition as _QuantityDefinition,
    QuantityAmount as _QuantityAmount, TermValue as _TermValue, EnumValue as _EnumValue)
from plumb.core.points import PointDeclaration as _PointDeclaration, PointRef as _PointRef, PointGroupRef as _PointGroupRef
from plumb.core.shape_constraints import ShapeValues as _ShapeValues
from plumb.qudt import units as _units, quantity_kinds as _kinds
ONTOLOGY = _OntologyInfo('ASM2d', 'https://watermetadata.org/plumb/asm2d#', source='ontology/asm2d.ttl')
_REGISTRY = _Registry(ONTOLOGY)
REGISTRY = _REGISTRY
_REGISTRY.by_name.update(_BASE._REGISTRY.by_name)
_REGISTRY.by_iri.update(_BASE._REGISTRY.by_iri)
_REGISTRY.enums_by_iri.update(_BASE._REGISTRY.enums_by_iri)
_REGISTRY.terms_by_iri.update(_BASE._REGISTRY.terms_by_iri)
_REGISTRY.containment.rules.extend(_BASE._REGISTRY.containment.rules)
_REGISTRY.sensor_classes.update(_BASE._REGISTRY.sensor_classes)
from pathlib import Path as _Path
from rdflib import Graph as _Graph
if '__file__' in globals():
    _REGISTRY.schema_graph = _Graph().parse(_Path(__file__).with_name('_shapes.ttl'))
_term_0 = _TermValue('https://watermetadata.org/plumb/asm2d#ComponentMassFlow', types=('https://watermetadata.org/plumb/asm2d#SplitBasis',), ontology_iri='https://watermetadata.org/plumb/asm2d#')
_term_1 = _TermValue('https://watermetadata.org/plumb/asm2d#OverallFlow', types=('https://watermetadata.org/plumb/asm2d#SplitBasis',), ontology_iri='https://watermetadata.org/plumb/asm2d#')
_REGISTRY.terms_by_iri.update({'https://watermetadata.org/plumb/asm2d#ComponentMassFlow': _term_0, 'https://watermetadata.org/plumb/asm2d#OverallFlow': _term_1})

class AerobicStage(_BASE.AerationBasin):
    'AerobicStage'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/asm2d#AerobicStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='AerobicStage',
        definition=None,
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='outlet', label='outlet'),),
    )
    _shape_constraints = (
        _ShapeValues('has_role', 'https://watermetadata.org/plumb/asm2d#AerobicStageShape/hasRole/3', required=(_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Role-Aerobic'], _BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Role-Secondary'],), defaults=(), choices=(), minimum=0, maximum=None),
        _ShapeValues('has_process', 'https://watermetadata.org/plumb/asm2d#AerobicStageShape/hasProcess/0', required=(_BASE.Process_Aeration, _BASE.Process_Nitrification,), defaults=(), choices=(), minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'https://watermetadata.org/plumb/asm2d#AerobicStageShape/ammonia-objective', required=(_BASE.TreatmentObjective_AmmoniaControl, _BASE.TreatmentObjective_NitrogenRemoval,), defaults=(), choices=(), minimum=0, maximum=None),
    )
    _shape_max_ports = 2
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='inlet')
    outlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='outlet')
    _point_declarations = {
        'inlet': inlet,
        'outlet': outlet,
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
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_BASE.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
        medium: _Iterable[_EnumValue] | None = None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'has_property': has_property,
            'medium': medium,
            'cnx': cnx,
            'connected': connected,
            'connected_from': connected_from,
            'connected_through': connected_through,
            'connected_to': connected_to,
            'has_connection_point': has_connection_point,
            'has_optional_connection_point': has_optional_connection_point,
            'actuated_by_property': actuated_by_property,
            'contains_': contains_,
            'executes': executes,
            'has_physical_location': has_physical_location,
            'has_process': has_process,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
        })

class AnaerobicStage(_BASE.Reactor):
    'AnaerobicStage'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/asm2d#AnaerobicStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='AnaerobicStage',
        definition=None,
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='outlet', label='outlet'),),
    )
    _shape_constraints = (
        _ShapeValues('has_role', 'https://watermetadata.org/plumb/asm2d#AnaerobicStageShape/hasRole/2', required=(_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Role-Anaerobic'], _BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Role-Secondary'],), defaults=(), choices=(), minimum=0, maximum=None),
        _ShapeValues('has_process', 'https://watermetadata.org/plumb/asm2d#AnaerobicStageShape/hasProcess/0', required=(_BASE.Process_EnhancedBiologicalPhosphorusRemoval,), defaults=(), choices=(), minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'https://watermetadata.org/plumb/asm2d#AnaerobicStageShape/hasTreatmentObjective/1', required=(_BASE.TreatmentObjective_PhosphorusRemoval,), defaults=(), choices=(), minimum=0, maximum=None),
    )
    _shape_max_ports = 2
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='inlet')
    outlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='outlet')
    _point_declarations = {
        'inlet': inlet,
        'outlet': outlet,
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
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_BASE.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
        medium: _Iterable[_EnumValue] | None = None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'has_property': has_property,
            'medium': medium,
            'cnx': cnx,
            'connected': connected,
            'connected_from': connected_from,
            'connected_through': connected_through,
            'connected_to': connected_to,
            'has_connection_point': has_connection_point,
            'has_optional_connection_point': has_optional_connection_point,
            'actuated_by_property': actuated_by_property,
            'contains_': contains_,
            'executes': executes,
            'has_physical_location': has_physical_location,
            'has_process': has_process,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
        })

class AnoxicStage(_BASE.Reactor):
    'AnoxicStage'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/asm2d#AnoxicStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='AnoxicStage',
        definition=None,
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='outlet', label='outlet'),),
    )
    _shape_constraints = (
        _ShapeValues('has_role', 'https://watermetadata.org/plumb/asm2d#AnoxicStageShape/hasRole/2', required=(_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Role-Anoxic'], _BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Role-Secondary'],), defaults=(), choices=(), minimum=0, maximum=None),
        _ShapeValues('has_process', 'https://watermetadata.org/plumb/asm2d#AnoxicStageShape/hasProcess/0', required=(_BASE.Process_Denitrification,), defaults=(), choices=(), minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'https://watermetadata.org/plumb/asm2d#AnoxicStageShape/hasTreatmentObjective/1', required=(_BASE.TreatmentObjective_NitrogenRemoval,), defaults=(), choices=(), minimum=0, maximum=None),
    )
    _shape_max_ports = 2
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='inlet')
    outlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='outlet')
    _point_declarations = {
        'inlet': inlet,
        'outlet': outlet,
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
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_BASE.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
        medium: _Iterable[_EnumValue] | None = None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'has_property': has_property,
            'medium': medium,
            'cnx': cnx,
            'connected': connected,
            'connected_from': connected_from,
            'connected_through': connected_through,
            'connected_to': connected_to,
            'has_connection_point': has_connection_point,
            'has_optional_connection_point': has_optional_connection_point,
            'actuated_by_property': actuated_by_property,
            'contains_': contains_,
            'executes': executes,
            'has_physical_location': has_physical_location,
            'has_process': has_process,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
        })

class InfluentMixer(_BASE.StaticMixer):
    'InfluentMixer'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/asm2d#InfluentMixer',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='InfluentMixer',
        definition=None,
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='feed_water', label='feed_water'), _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='recycle', label='recycle'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='outlet', label='outlet'),),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'https://watermetadata.org/plumb/asm2d#InfluentMixerShape/hasProcess/0', required=(_BASE.Process_Mixing,), defaults=(), choices=(), minimum=1, maximum=None),
    )
    _shape_max_ports = 3
    feed_water = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='feed_water')
    recycle = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='recycle')
    outlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='outlet')
    _point_declarations = {
        'feed_water': feed_water,
        'recycle': recycle,
        'outlet': outlet,
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
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_BASE.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
        medium: _Iterable[_EnumValue] | None = None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'has_property': has_property,
            'medium': medium,
            'cnx': cnx,
            'connected': connected,
            'connected_from': connected_from,
            'connected_through': connected_through,
            'connected_to': connected_to,
            'has_connection_point': has_connection_point,
            'has_optional_connection_point': has_optional_connection_point,
            'actuated_by_property': actuated_by_property,
            'contains_': contains_,
            'executes': executes,
            'has_physical_location': has_physical_location,
            'has_process': has_process,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
        })

class InternalRecycleSplitter(_BASE.Junction):
    'InternalRecycleSplitter'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/asm2d#InternalRecycleSplitter',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='InternalRecycleSplitter',
        definition=None,
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='overflow', label='overflow'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='underflow', label='underflow'),),
    )
    _shape_constraints = (
        _ShapeValues('medium', 'https://watermetadata.org/plumb/asm2d#InternalRecycleSplitterShape/hasMedium/0', required=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'],), defaults=(), choices=(), minimum=1, maximum=1),
    )
    _shape_max_ports = 3
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='inlet')
    overflow = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='overflow')
    underflow = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='underflow')
    _point_declarations = {
        'inlet': inlet,
        'overflow': overflow,
        'underflow': underflow,
    }
    def __init__(self, name: str | None = None, *,
        cnx: _Iterable[_BASE.ConnectionPoint] | None = None,
        connected: _Iterable[_BASE.Connectable] | None = None,
        connected_from: _Iterable[_BASE.Connectable] | None = None,
        connected_through: _Iterable[_BASE.Connection] | None = None,
        connected_to: _Iterable[_BASE.Connectable] | None = None,
        has_connection_point: _Iterable[_BASE.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_BASE.ConnectionPoint] | None = None,
        has_property: _Iterable[_BASE.Property] | None = None,
        medium: _EnumValue | None = None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'has_property': has_property,
            'medium': medium,
            'cnx': cnx,
            'connected': connected,
            'connected_from': connected_from,
            'connected_through': connected_through,
            'connected_to': connected_to,
            'has_connection_point': has_connection_point,
            'has_optional_connection_point': has_optional_connection_point,
        })

class RecycleMixer(_BASE.StaticMixer):
    'RecycleMixer'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/asm2d#RecycleMixer',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='RecycleMixer',
        definition=None,
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='reactor', label='reactor'), _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='internal_recycle', label='internal_recycle'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='outlet', label='outlet'),),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'https://watermetadata.org/plumb/asm2d#RecycleMixerShape/hasProcess/0', required=(_BASE.Process_Mixing,), defaults=(), choices=(), minimum=1, maximum=None),
    )
    _shape_max_ports = 3
    reactor = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='reactor')
    internal_recycle = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='internal_recycle')
    outlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='outlet')
    _point_declarations = {
        'reactor': reactor,
        'internal_recycle': internal_recycle,
        'outlet': outlet,
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
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_BASE.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
        medium: _Iterable[_EnumValue] | None = None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'has_property': has_property,
            'medium': medium,
            'cnx': cnx,
            'connected': connected,
            'connected_from': connected_from,
            'connected_through': connected_through,
            'connected_to': connected_to,
            'has_connection_point': has_connection_point,
            'has_optional_connection_point': has_optional_connection_point,
            'actuated_by_property': actuated_by_property,
            'contains_': contains_,
            'executes': executes,
            'has_physical_location': has_physical_location,
            'has_process': has_process,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
        })

class RecyclePump(_BASE.Pump):
    'RecyclePump'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/asm2d#RecyclePump',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='RecyclePump',
        definition=None,
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='outlet', label='outlet'),),
    )
    _shape_max_ports = 2
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='inlet')
    outlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='outlet')
    _point_declarations = {
        'inlet': inlet,
        'outlet': outlet,
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
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_BASE.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
        medium: _Iterable[_EnumValue] | None = None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'has_property': has_property,
            'medium': medium,
            'cnx': cnx,
            'connected': connected,
            'connected_from': connected_from,
            'connected_through': connected_through,
            'connected_to': connected_to,
            'has_connection_point': has_connection_point,
            'has_optional_connection_point': has_optional_connection_point,
            'actuated_by_property': actuated_by_property,
            'contains_': contains_,
            'executes': executes,
            'has_physical_location': has_physical_location,
            'has_process': has_process,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
        })

class SecondaryClarifier(_BASE.SedimentationTank):
    'SecondaryClarifier'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/asm2d#SecondaryClarifier',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='SecondaryClarifier',
        definition=None,
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='effluent', label='effluent'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='underflow', label='underflow'),),
    )
    _shape_constraints = (
        _ShapeValues('has_role', 'https://watermetadata.org/plumb/asm2d#SecondaryClarifierShape/hasRole/2', required=(_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Role-Secondary'],), defaults=(), choices=(), minimum=0, maximum=None),
        _ShapeValues('has_process', 'https://watermetadata.org/plumb/asm2d#SecondaryClarifierShape/hasProcess/0', required=(_BASE.Process_Settling,), defaults=(), choices=(), minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'https://watermetadata.org/plumb/asm2d#SecondaryClarifierShape/hasTreatmentObjective/1', required=(_BASE.TreatmentObjective_Clarification,), defaults=(), choices=(), minimum=0, maximum=None),
    )
    _shape_max_ports = 3
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='inlet')
    effluent = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='effluent')
    underflow = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='underflow')
    _point_declarations = {
        'inlet': inlet,
        'effluent': effluent,
        'underflow': underflow,
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
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_BASE.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
        medium: _Iterable[_EnumValue] | None = None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'has_property': has_property,
            'medium': medium,
            'cnx': cnx,
            'connected': connected,
            'connected_from': connected_from,
            'connected_through': connected_through,
            'connected_to': connected_to,
            'has_connection_point': has_connection_point,
            'has_optional_connection_point': has_optional_connection_point,
            'actuated_by_property': actuated_by_property,
            'contains_': contains_,
            'executes': executes,
            'has_physical_location': has_physical_location,
            'has_process': has_process,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
        })

class SludgeSplitter(_BASE.Junction):
    'SludgeSplitter'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/asm2d#SludgeSplitter',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='SludgeSplitter',
        definition=None,
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='recycle', label='recycle'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='waste', label='waste'),),
    )
    _shape_constraints = (
        _ShapeValues('medium', 'https://watermetadata.org/plumb/asm2d#SludgeSplitterShape/hasMedium/0', required=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'],), defaults=(), choices=(), minimum=1, maximum=1),
    )
    _shape_max_ports = 3
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='inlet')
    recycle = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='recycle')
    waste = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='waste')
    _point_declarations = {
        'inlet': inlet,
        'recycle': recycle,
        'waste': waste,
    }
    def __init__(self, name: str | None = None, *,
        cnx: _Iterable[_BASE.ConnectionPoint] | None = None,
        connected: _Iterable[_BASE.Connectable] | None = None,
        connected_from: _Iterable[_BASE.Connectable] | None = None,
        connected_through: _Iterable[_BASE.Connection] | None = None,
        connected_to: _Iterable[_BASE.Connectable] | None = None,
        has_connection_point: _Iterable[_BASE.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_BASE.ConnectionPoint] | None = None,
        has_property: _Iterable[_BASE.Property] | None = None,
        medium: _EnumValue | None = None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'has_property': has_property,
            'medium': medium,
            'cnx': cnx,
            'connected': connected,
            'connected_from': connected_from,
            'connected_through': connected_through,
            'connected_to': connected_to,
            'has_connection_point': has_connection_point,
            'has_optional_connection_point': has_optional_connection_point,
        })

class SplitFraction(_BASE.QuantifiableProperty):
    'SplitFraction'
    _spec_has_split_basis = _PropertySpec(name='has_split_basis', predicate='https://watermetadata.org/plumb/asm2d#hasSplitBasis', kind='term', max_count=1, term_ranges=('https://watermetadata.org/plumb/asm2d#SplitBasis',), datatype=None)
    has_split_basis: _TermOne[_TermValue] = _TermOne(_spec_has_split_basis)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/asm2d#SplitFraction',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label=None,
        definition=None,
        properties=(_spec_has_split_basis,),
    )
    _shape_constraints = (
        _ShapeValues('has_split_basis', 'https://watermetadata.org/plumb/asm2d#SplitFractionShape/hasSplitBasis/0', required=(), defaults=(), choices=(), minimum=1, maximum=1),
    )
    def __init__(self, name: str | None = None, *,
        has_accuracy: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_aggregation: _EnumValue | None = None,
        has_alarm_status: _Iterable[_BASE.EnumerableProperty] | None = None,
        has_aspect: _Iterable[_EnumValue] | None = None,
        has_bias: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_calibration_curve: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_deadband: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_drop_rate: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_external_reference: _Iterable[_BASE.ExternalReference] | None = None,
        has_internal_reference: _Iterable[_BASE.Property] | None = None,
        has_measurement_range: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_numeric_range: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_numeric_resolution: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_precision: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_processed_data: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_property: _Iterable[_BASE.Property] | None = None,
        has_quantity_kind: _BASE.QuantityKind | None,
        has_response_time: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_setpoint: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_split_basis: _TermValue | None,
        has_temporal_range: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_temporal_resolution: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_threshold: _Iterable[_BASE.QuantifiableProperty] | None = None,
        has_unit: _BASE.Unit | None = None,
        has_value: object | None = None,
        has_variable_range: _Iterable[_BASE.QuantifiableProperty] | None = None,
        is_delta_quantity: bool | None = None,
        is_internal_reference_of: _BASE.Property | None = None,
        medium: _Iterable[_EnumValue] | None = None,
        of_constituent: _Iterable[_Entity] | None = None,
        of_medium: _EnumValue | None = None,
        of_substance: _EnumValue | None = None,
        quantity_value: _Iterable[_BASE.QuantityValue] | None = None,
        value: _Iterable[_Entity] | None = None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'has_property': has_property,
            'medium': medium,
            'has_aspect': has_aspect,
            'has_external_reference': has_external_reference,
            'has_internal_reference': has_internal_reference,
            'has_value': has_value,
            'is_internal_reference_of': is_internal_reference_of,
            'of_constituent': of_constituent,
            'of_medium': of_medium,
            'of_substance': of_substance,
            'has_accuracy': has_accuracy,
            'has_aggregation': has_aggregation,
            'has_alarm_status': has_alarm_status,
            'has_bias': has_bias,
            'has_calibration_curve': has_calibration_curve,
            'has_deadband': has_deadband,
            'has_drop_rate': has_drop_rate,
            'has_measurement_range': has_measurement_range,
            'has_numeric_range': has_numeric_range,
            'has_numeric_resolution': has_numeric_resolution,
            'has_precision': has_precision,
            'has_processed_data': has_processed_data,
            'has_quantity_kind': has_quantity_kind,
            'has_response_time': has_response_time,
            'has_setpoint': has_setpoint,
            'has_temporal_range': has_temporal_range,
            'has_temporal_resolution': has_temporal_resolution,
            'has_threshold': has_threshold,
            'has_unit': has_unit,
            'has_variable_range': has_variable_range,
            'is_delta_quantity': is_delta_quantity,
            'quantity_value': quantity_value,
            'value': value,
            'has_split_basis': has_split_basis,
        })

@_dataclass(frozen=True, kw_only=True)
class ASM2dState(_PropertySchema):
    'Nominal influent conditions: flow in m³/day, temperature in K, pressure in Pa, component pools in g/m³, and alkalinity in mol/m³. Component pools retain their defined COD, nitrogen, phosphorus, or solids basis.'
    source_shape = 'https://watermetadata.org/plumb/asm2d#ASM2dStateShape'
    _definitions = (
        _QuantityDefinition(name='flow_rate', source_shape='https://watermetadata.org/plumb/asm2d#FlowRateShape', kind=_kinds.VolumeFlowRate, unit=_units.M3_PER_DAY, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Flow rate', allowed_units=(_units.M3_PER_DAY, _units.M3_PER_SEC, _units.L_PER_SEC,), description=None, notation=None, local_name=None, minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), properties=()),
        _QuantityDefinition(name='temperature', source_shape='https://watermetadata.org/plumb/asm2d#TemperatureShape', kind=_kinds.Temperature, unit=_units.K, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Temperature', allowed_units=(_units.K, _units.DEG_C,), description=None, notation=None, local_name=None, minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), properties=()),
        _QuantityDefinition(name='pressure', source_shape='https://watermetadata.org/plumb/asm2d#PressureShape', kind=_kinds.Pressure, unit=_units.PA, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Pressure', allowed_units=(_units.PA, _units.KiloPA, _units.BAR,), description=None, notation=None, local_name=None, minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), properties=()),
        _QuantityDefinition(name='dissolved_oxygen', source_shape='https://watermetadata.org/plumb/asm2d#DissolvedOxygenShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Dissolved oxygen', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='Molecular oxygen dissolved in a treatment medium.', notation='S_O2', local_name='s_o2-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-DissolvedOxygen'], properties=()),
        _QuantityDefinition(name='fermentable_substrate', source_shape='https://watermetadata.org/plumb/asm2d#FermentableSubstrateShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Fermentable substrate', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='S_F: soluble, readily biodegradable fermentable organic substrate pool in ASM2d, expressed on a COD basis.', notation='S_F', local_name='s_f-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-S_F'], properties=()),
        _QuantityDefinition(name='fermentation_products', source_shape='https://watermetadata.org/plumb/asm2d#FermentationProductsShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Fermentation products', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='S_A: soluble fermentation products represented as acetate in ASM2d, expressed on a COD basis; not a pure acetate concentration.', notation='S_A', local_name='s_a-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-S_A'], properties=()),
        _QuantityDefinition(name='ammonia_ammonium_nitrogen', source_shape='https://watermetadata.org/plumb/asm2d#AmmoniaAmmoniumNitrogenShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Ammonia ammonium nitrogen', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='S_NH4: combined ammonium and ammonia nitrogen pool in ASM2d, expressed as nitrogen rather than pure NH3 mass.', notation='S_NH4', local_name='s_nh4-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-S_NH4'], properties=()),
        _QuantityDefinition(name='nitrate_nitrite_nitrogen', source_shape='https://watermetadata.org/plumb/asm2d#NitrateNitriteNitrogenShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Nitrate nitrite nitrogen', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='S_NO3: combined nitrate and nitrite nitrogen pool in ASM2d, expressed as nitrogen; neither nitrate nor nitrite alone.', notation='S_NO3', local_name='s_no3-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-S_NO3'], properties=()),
        _QuantityDefinition(name='soluble_inorganic_phosphorus', source_shape='https://watermetadata.org/plumb/asm2d#SolubleInorganicPhosphorusShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Soluble inorganic phosphorus', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='S_PO4: soluble inorganic phosphorus pool in ASM2d, primarily orthophosphate, expressed as phosphorus.', notation='S_PO4', local_name='s_po4-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-S_PO4'], properties=()),
        _QuantityDefinition(name='inert_soluble_organics', source_shape='https://watermetadata.org/plumb/asm2d#InertSolubleOrganicsShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Inert soluble organics', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='S_I: inert soluble organic material pool in ASM2d.', notation='S_I', local_name='s_i-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-S_I'], properties=()),
        _QuantityDefinition(name='dissolved_nitrogen', source_shape='https://watermetadata.org/plumb/asm2d#DissolvedNitrogenShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Dissolved nitrogen', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='Nitrogen', notation='S_N2', local_name='s_n2-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Constituent-N2'], properties=()),
        _QuantityDefinition(name='inert_particulate_organics', source_shape='https://watermetadata.org/plumb/asm2d#InertParticulateOrganicsShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Inert particulate organics', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='X_I: inert particulate organic material pool in ASM2d.', notation='X_I', local_name='x_i-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-X_I'], properties=()),
        _QuantityDefinition(name='slowly_biodegradable_substrate', source_shape='https://watermetadata.org/plumb/asm2d#SlowlyBiodegradableSubstrateShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Slowly biodegradable substrate', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='X_S: slowly biodegradable particulate substrate pool in ASM2d.', notation='X_S', local_name='x_s-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-X_S'], properties=()),
        _QuantityDefinition(name='heterotrophic_biomass', source_shape='https://watermetadata.org/plumb/asm2d#HeterotrophicBiomassShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Heterotrophic biomass', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='X_H: heterotrophic organism biomass pool in ASM2d.', notation='X_H', local_name='x_h-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-X_H'], properties=()),
        _QuantityDefinition(name='phosphate_accumulating_biomass', source_shape='https://watermetadata.org/plumb/asm2d#PhosphateAccumulatingBiomassShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Phosphate accumulating biomass', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='X_PAO: phosphate-accumulating organism biomass pool in ASM2d.', notation='X_PAO', local_name='x_pao-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-X_PAO'], properties=()),
        _QuantityDefinition(name='stored_polyphosphate', source_shape='https://watermetadata.org/plumb/asm2d#StoredPolyphosphateShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Stored polyphosphate', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='X_PP: intracellular polyphosphate storage pool of phosphate-accumulating organisms in ASM2d.', notation='X_PP', local_name='x_pp-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-X_PP'], properties=()),
        _QuantityDefinition(name='stored_pha', source_shape='https://watermetadata.org/plumb/asm2d#StoredPhaShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Stored pha', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='X_PHA: intracellular polyhydroxyalkanoate storage pool of phosphate-accumulating organisms in ASM2d.', notation='X_PHA', local_name='x_pha-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-X_PHA'], properties=()),
        _QuantityDefinition(name='autotrophic_biomass', source_shape='https://watermetadata.org/plumb/asm2d#AutotrophicBiomassShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Autotrophic biomass', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='X_AUT: autotrophic nitrifying organism biomass pool in ASM2d.', notation='X_AUT', local_name='x_aut-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-X_AUT'], properties=()),
        _QuantityDefinition(name='metal_hydroxides', source_shape='https://watermetadata.org/plumb/asm2d#MetalHydroxidesShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Metal hydroxides', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='X_MeOH: metal hydroxide particulate pool in ASM2d.', notation='X_MeOH', local_name='x_meoh-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-X_MeOH'], properties=()),
        _QuantityDefinition(name='metal_phosphates', source_shape='https://watermetadata.org/plumb/asm2d#MetalPhosphatesShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Metal phosphates', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='X_MeP: metal phosphate particulate pool in ASM2d.', notation='X_MeP', local_name='x_mep-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-ASM2d-X_MeP'], properties=()),
        _QuantityDefinition(name='total_suspended_solids', source_shape='https://watermetadata.org/plumb/asm2d#TotalSuspendedSolidsShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Total suspended solids', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='Solid particulate matter suspended in water rather than dissolved, including organic and inorganic material carried in the fluid.', notation='X_TSS', local_name='x_tss-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-SuspendedSolids'], properties=()),
        _QuantityDefinition(name='alkalinity', source_shape='https://watermetadata.org/plumb/asm2d#AlkalinityShape', kind=_kinds.AmountOfSubstanceConcentration, unit=_units.MOL_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Alkalinity', allowed_units=(_units.MOL_PER_M3, _units.KiloMOL_PER_M3,), description=None, notation='S_ALK', local_name='s_alk-concentration', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], properties=()),
    )
    flow_rate: float | _QuantityAmount
    'Flow rate; ; default unit http://qudt.org/vocab/unit/M3-PER-DAY; source https://watermetadata.org/plumb/asm2d#FlowRateShape'
    temperature: float | _QuantityAmount
    'Temperature; ; default unit http://qudt.org/vocab/unit/K; source https://watermetadata.org/plumb/asm2d#TemperatureShape'
    pressure: float | _QuantityAmount
    'Pressure; ; default unit http://qudt.org/vocab/unit/PA; source https://watermetadata.org/plumb/asm2d#PressureShape'
    dissolved_oxygen: float | _QuantityAmount
    'Dissolved oxygen; S_O2; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#DissolvedOxygenShape'
    fermentable_substrate: float | _QuantityAmount
    'Fermentable substrate; S_F; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#FermentableSubstrateShape'
    fermentation_products: float | _QuantityAmount
    'Fermentation products; S_A; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#FermentationProductsShape'
    ammonia_ammonium_nitrogen: float | _QuantityAmount
    'Ammonia ammonium nitrogen; S_NH4; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#AmmoniaAmmoniumNitrogenShape'
    nitrate_nitrite_nitrogen: float | _QuantityAmount
    'Nitrate nitrite nitrogen; S_NO3; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#NitrateNitriteNitrogenShape'
    soluble_inorganic_phosphorus: float | _QuantityAmount
    'Soluble inorganic phosphorus; S_PO4; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#SolubleInorganicPhosphorusShape'
    inert_soluble_organics: float | _QuantityAmount
    'Inert soluble organics; S_I; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#InertSolubleOrganicsShape'
    dissolved_nitrogen: float | _QuantityAmount
    'Dissolved nitrogen; S_N2; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#DissolvedNitrogenShape'
    inert_particulate_organics: float | _QuantityAmount
    'Inert particulate organics; X_I; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#InertParticulateOrganicsShape'
    slowly_biodegradable_substrate: float | _QuantityAmount
    'Slowly biodegradable substrate; X_S; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#SlowlyBiodegradableSubstrateShape'
    heterotrophic_biomass: float | _QuantityAmount
    'Heterotrophic biomass; X_H; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#HeterotrophicBiomassShape'
    phosphate_accumulating_biomass: float | _QuantityAmount
    'Phosphate accumulating biomass; X_PAO; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#PhosphateAccumulatingBiomassShape'
    stored_polyphosphate: float | _QuantityAmount
    'Stored polyphosphate; X_PP; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#StoredPolyphosphateShape'
    stored_pha: float | _QuantityAmount
    'Stored pha; X_PHA; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#StoredPhaShape'
    autotrophic_biomass: float | _QuantityAmount
    'Autotrophic biomass; X_AUT; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#AutotrophicBiomassShape'
    metal_hydroxides: float | _QuantityAmount
    'Metal hydroxides; X_MeOH; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#MetalHydroxidesShape'
    metal_phosphates: float | _QuantityAmount
    'Metal phosphates; X_MeP; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#MetalPhosphatesShape'
    total_suspended_solids: float | _QuantityAmount
    'Total suspended solids; X_TSS; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#TotalSuspendedSolidsShape'
    alkalinity: float | _QuantityAmount
    'Alkalinity; S_ALK; default unit http://qudt.org/vocab/unit/MOL-PER-M3; source https://watermetadata.org/plumb/asm2d#AlkalinityShape'

@_dataclass(frozen=True, kw_only=True)
class AerobicDesign(_PropertySchema):
    'Aerobic basin volume in m³ (default 1333) and oxygen transfer coefficient KLa in h⁻¹.'
    source_shape = 'https://watermetadata.org/plumb/asm2d#AerobicDesignShape'
    _definitions = (
        _QuantityDefinition(name='volume', source_shape='https://watermetadata.org/plumb/asm2d#AerobicVolumeShape', kind=_kinds.Volume, unit=_units.M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Volume', allowed_units=(_units.M3, _units.L,), description=None, notation=None, local_name=None, minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), properties=()),
        _QuantityDefinition(name='oxygen_transfer_coefficient', source_shape='https://watermetadata.org/plumb/asm2d#OxygenTransferCoefficientShape', kind=_kinds.Frequency, unit=_units.PER_HR, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Oxygen transfer coefficient', allowed_units=(_units.PER_HR, _units.PER_SEC, _units.PER_DAY,), description=None, notation=None, local_name=None, minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), properties=()),
    )
    volume: float | _QuantityAmount = 1333.0
    'Volume; ; default unit http://qudt.org/vocab/unit/M3; source https://watermetadata.org/plumb/asm2d#AerobicVolumeShape'
    oxygen_transfer_coefficient: float | _QuantityAmount
    'Oxygen transfer coefficient; ; default unit http://qudt.org/vocab/unit/PER-HR; source https://watermetadata.org/plumb/asm2d#OxygenTransferCoefficientShape'

@_dataclass(frozen=True, kw_only=True)
class ClarifierEffluentSplit(_PropertySchema):
    'Fractions of incoming H2O and suspended-solids mass flows routed to effluent; dimensionless.'
    source_shape = 'https://watermetadata.org/plumb/asm2d#ClarifierEffluentSplitShape'
    _definitions = (
        _QuantityDefinition(name='h2o_fraction', source_shape='https://watermetadata.org/plumb/asm2d#H2OComponentFractionShape', kind=_kinds.DimensionlessRatio, unit=_units.UNITLESS, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='H2o fraction', allowed_units=(_units.UNITLESS,), description='Pure water', notation=None, local_name=None, minimum=0.0, maximum=1.0, allowed_values=(), property_class=SplitFraction, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Constituent-H2O'], properties=(('has_split_basis', _term_0),)),
        _QuantityDefinition(name='tss_fraction', source_shape='https://watermetadata.org/plumb/asm2d#TSSComponentFractionShape', kind=_kinds.DimensionlessRatio, unit=_units.UNITLESS, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Tss fraction', allowed_units=(_units.UNITLESS,), description='Solid particulate matter suspended in water rather than dissolved, including organic and inorganic material carried in the fluid.', notation=None, local_name=None, minimum=0.0, maximum=1.0, allowed_values=(), property_class=SplitFraction, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-SuspendedSolids'], properties=(('has_split_basis', _term_0),)),
    )
    h2o_fraction: float | _QuantityAmount
    'H2o fraction; ; default unit http://qudt.org/vocab/unit/UNITLESS; source https://watermetadata.org/plumb/asm2d#H2OComponentFractionShape'
    tss_fraction: float | _QuantityAmount
    'Tss fraction; ; default unit http://qudt.org/vocab/unit/UNITLESS; source https://watermetadata.org/plumb/asm2d#TSSComponentFractionShape'

@_dataclass(frozen=True, kw_only=True)
class OverallFlowSplit(_PropertySchema):
    'Fraction of the incoming overall flow routed to this outlet; dimensionless.'
    source_shape = 'https://watermetadata.org/plumb/asm2d#OverallFlowSplitShape'
    _definitions = (
        _QuantityDefinition(name='fraction', source_shape='https://watermetadata.org/plumb/asm2d#OverallFlowFractionShape', kind=_kinds.DimensionlessRatio, unit=_units.UNITLESS, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Fraction', allowed_units=(_units.UNITLESS,), description=None, notation=None, local_name=None, minimum=0.0, maximum=1.0, allowed_values=(), property_class=SplitFraction, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), properties=(('has_split_basis', _term_1),)),
    )
    fraction: float | _QuantityAmount
    'Fraction; ; default unit http://qudt.org/vocab/unit/UNITLESS; source https://watermetadata.org/plumb/asm2d#OverallFlowFractionShape'

@_dataclass(frozen=True, kw_only=True)
class OxygenOutletState(_PropertySchema):
    'Reference dissolved oxygen concentration in outlet water, in g/m³.'
    source_shape = 'https://watermetadata.org/plumb/asm2d#OxygenOutletStateShape'
    _definitions = (
        _QuantityDefinition(name='oxygen_concentration', source_shape='https://watermetadata.org/plumb/asm2d#DissolvedOxygenShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Oxygen concentration', allowed_units=(_units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L, _units.GM_PER_L,), description='Molecular oxygen dissolved in a treatment medium.', notation='S_O2', local_name=None, minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), of_medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], of_substance=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Constituent-DissolvedOxygen'], properties=()),
    )
    oxygen_concentration: float | _QuantityAmount
    'Oxygen concentration; S_O2; default unit http://qudt.org/vocab/unit/GM-PER-M3; source https://watermetadata.org/plumb/asm2d#DissolvedOxygenShape'

@_dataclass(frozen=True, kw_only=True)
class PressureState(_PropertySchema):
    'Nominal pressure in Pa.'
    source_shape = 'https://watermetadata.org/plumb/asm2d#PressureStateShape'
    _definitions = (
        _QuantityDefinition(name='pressure', source_shape='https://watermetadata.org/plumb/asm2d#PressureShape', kind=_kinds.Pressure, unit=_units.PA, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Pressure', allowed_units=(_units.PA, _units.KiloPA, _units.BAR,), description=None, notation=None, local_name=None, minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), properties=()),
    )
    pressure: float | _QuantityAmount
    'Pressure; ; default unit http://qudt.org/vocab/unit/PA; source https://watermetadata.org/plumb/asm2d#PressureShape'

@_dataclass(frozen=True, kw_only=True)
class ReactorDesign(_PropertySchema):
    'Nominal reactor design volume in m³.'
    source_shape = 'https://watermetadata.org/plumb/asm2d#ReactorDesignShape'
    _definitions = (
        _QuantityDefinition(name='volume', source_shape='https://watermetadata.org/plumb/asm2d#ReactorVolumeShape', kind=_kinds.Volume, unit=_units.M3, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Volume', allowed_units=(_units.M3, _units.L,), description=None, notation=None, local_name=None, minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Aspect-Nominal'],), properties=()),
    )
    volume: float | _QuantityAmount
    'Volume; ; default unit http://qudt.org/vocab/unit/M3; source https://watermetadata.org/plumb/asm2d#ReactorVolumeShape'

__all__ = ['ONTOLOGY', 'REGISTRY', 'AerobicStage', 'AnaerobicStage', 'AnoxicStage', 'InfluentMixer', 'InternalRecycleSplitter', 'RecycleMixer', 'RecyclePump', 'SecondaryClarifier', 'SludgeSplitter', 'SplitFraction', 'ASM2dState', 'AerobicDesign', 'ClarifierEffluentSplit', 'OverallFlowSplit', 'OxygenOutletState', 'PressureState', 'ReactorDesign']
