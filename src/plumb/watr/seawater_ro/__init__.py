"""SeawaterRO: generated from RDF/SHACL. DO NOT EDIT."""
# ruff: noqa
from __future__ import annotations
from dataclasses import dataclass as _dataclass
from typing import Iterable as _Iterable
import plumb.watr as _BASE
import plumb.s223 as _DEP0
from plumb.core import (Entity as _Entity, ClassInfo as _ClassInfo, CPSlot as _CPSlot,
    Model as _Model, Registry as _Registry, OntologyInfo as _OntologyInfo,
    PropertySpec as _PropertySpec, TermOne as _TermOne, Lit as _Lit, Rel as _Rel, RelOne as _RelOne, EnumOne as _EnumOne, EnumSet as _EnumSet, ValueOne as _ValueOne,
    PropertySchema as _PropertySchema, QuantityDefinition as _QuantityDefinition,
    QuantityAmount as _QuantityAmount, TermValue as _TermValue, EnumValue as _EnumValue, DeferredEndpoint as _DeferredEndpoint)
from plumb.core.points import PointDeclaration as _PointDeclaration, PointRef as _PointRef, PointGroupRef as _PointGroupRef
from plumb.core.shape_constraints import ShapeValues as _ShapeValues
from plumb.qudt import units as _units, quantity_kinds as _kinds
ONTOLOGY = _OntologyInfo('SeawaterRO', 'https://watermetadata.org/plumb/seawater-ro#', source='ontology/seawater-ro.ttl')
_REGISTRY = _Registry(ONTOLOGY)
REGISTRY = _REGISTRY
_REGISTRY.include(_BASE.REGISTRY)
from pathlib import Path as _Path
from rdflib import Graph as _Graph
if '__file__' in globals():
    _REGISTRY.schema_graph = _Graph().parse(_Path(__file__).with_name('_shapes.ttl'))
_REGISTRY.terms_by_iri.update({})

class AdvancedOxidationStage(_BASE.UVH2O2Reactor):
    'Advanced Oxidation Stage configuration defined by the seawater RO shapes.'
    _spec_has_process = _PropertySpec(
        name='has_process',
        predicate='https://watermetadata.org/ontology/watr#hasProcess',
        kind='class',
        label='has process',
        definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
        ranges=('Process',),
        range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
        sources=('bc09fac0c70bc9398630ec2a2', 'https://watermetadata.org/ontology/watr#hasProcess', 'https://watermetadata.org/plumb/seawater-ro#AdvancedOxidationStageShape/hasProcess/0'),
        min_count=1,
        required=True,
    )
    has_process: _Rel[type[_BASE.Process]] = _Rel(_spec_has_process)
    _spec_has_property = _PropertySpec(
        name='has_property',
        predicate='http://data.ashrae.org/standard223#hasProperty',
        kind='object',
        label='has property',
        definition='A `Relation` that associates a `Concept` with a `Property`.',
        ranges=('Property',),
        range_groups=(('http://data.ashrae.org/standard223#Property',),),
        sources=('b894486338780f2f7730cd6ec', 'https://watermetadata.org/plumb/seawater-ro#UVDesignShape/hasProperty/0', 'https://watermetadata.org/plumb/seawater-ro#UVDesignShape/hasProperty/1'),
    )
    has_property: _Rel[_DEP0.Property] = _Rel(_spec_has_property)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#AdvancedOxidationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Advanced Oxidation Stage',
        definition='Advanced Oxidation Stage configuration defined by the seawater RO shapes.',
        properties=(_spec_has_process, _spec_has_property,),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, https://watermetadata.org/ontology/watr#hasProcess, https://watermetadata.org/plumb/seawater-ro#AdvancedOxidationStageShape/hasProcess/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-AdvancedOxidation', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class BackwashSeparator(_BASE.UnitProcess):
    'Backwash Separator configuration defined by the seawater RO shapes.'
    _spec_has_process = _PropertySpec(
        name='has_process',
        predicate='https://watermetadata.org/ontology/watr#hasProcess',
        kind='class',
        label='has process',
        definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
        ranges=('Process',),
        range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
        sources=('bc09fac0c70bc9398630ec2a2', 'https://watermetadata.org/ontology/watr#hasProcess', 'https://watermetadata.org/plumb/seawater-ro#BackwashSeparatorShape/hasProcess/0'),
        min_count=1,
        required=True,
    )
    has_process: _Rel[type[_BASE.Process]] = _Rel(_spec_has_process)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#BackwashSeparator',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Backwash Separator',
        definition='Backwash Separator configuration defined by the seawater RO shapes.',
        properties=(_spec_has_process,),
        cp_slots=(_CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='https://watermetadata.org/ontology/watr#Fluid-Sludge', min_count=1, max_count=1, name='byproduct', label='byproduct'), _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='treated', label='treated'),),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, https://watermetadata.org/ontology/watr#hasProcess, https://watermetadata.org/plumb/seawater-ro#BackwashSeparatorShape/hasProcess/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-Separation', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
    )
    _shape_max_ports = 3
    byproduct = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('https://watermetadata.org/ontology/watr#Fluid-Sludge'), direction='out', label='byproduct')
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='inlet')
    treated = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='treated')
    _point_declarations = {
        'byproduct': byproduct,
        'inlet': inlet,
        'treated': treated,
    }
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class BackwashStage(_BASE.UnitProcess):
    'Backwash Stage configuration defined by the seawater RO shapes.'
    _spec_has_process = _PropertySpec(
        name='has_process',
        predicate='https://watermetadata.org/ontology/watr#hasProcess',
        kind='class',
        label='has process',
        definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
        ranges=('Process',),
        range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
        sources=('bc09fac0c70bc9398630ec2a2', 'https://watermetadata.org/ontology/watr#hasProcess', 'https://watermetadata.org/plumb/seawater-ro#BackwashStageShape/hasProcess/0'),
        min_count=1,
        required=True,
    )
    has_process: _Rel[type[_BASE.Process]] = _Rel(_spec_has_process)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#BackwashStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Backwash Stage',
        definition='Backwash Stage configuration defined by the seawater RO shapes.',
        properties=(_spec_has_process,),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, https://watermetadata.org/ontology/watr#hasProcess, https://watermetadata.org/plumb/seawater-ro#BackwashStageShape/hasProcess/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-Backwashing', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class BoosterPump(_BASE.Pump):
    'Booster Pump configuration defined by the seawater RO shapes.'
    _spec_has_property = _PropertySpec(
        name='has_property',
        predicate='http://data.ashrae.org/standard223#hasProperty',
        kind='object',
        label='has property',
        definition='A `Relation` that associates a `Concept` with a `Property`.',
        ranges=('Property',),
        range_groups=(('http://data.ashrae.org/standard223#Property',),),
        sources=('b894486338780f2f7730cd6ec', 'https://watermetadata.org/plumb/seawater-ro#PumpDesignShape/hasProperty/0'),
    )
    has_property: _Rel[_DEP0.Property] = _Rel(_spec_has_property)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#BoosterPump',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Booster Pump',
        definition='Booster Pump configuration defined by the seawater RO shapes.',
        properties=(_spec_has_property,),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class CartridgeFiltrationStage(_BASE.CartridgeFiltrationUnit):
    'Cartridge Filtration Stage configuration defined by the seawater RO shapes.'
    _spec_has_process = _PropertySpec(
        name='has_process',
        predicate='https://watermetadata.org/ontology/watr#hasProcess',
        kind='class',
        label='has process',
        definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
        ranges=('Process',),
        range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
        sources=('bc09fac0c70bc9398630ec2a2', 'https://watermetadata.org/ontology/watr#hasProcess', 'https://watermetadata.org/plumb/seawater-ro#CartridgeFiltrationStageShape/hasProcess/0'),
        min_count=1,
        required=True,
    )
    has_process: _Rel[type[_BASE.Process]] = _Rel(_spec_has_process)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#CartridgeFiltrationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Cartridge Filtration Stage',
        definition='Cartridge Filtration Stage configuration defined by the seawater RO shapes.',
        properties=(_spec_has_process,),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, https://watermetadata.org/ontology/watr#hasProcess, https://watermetadata.org/plumb/seawater-ro#CartridgeFiltrationStageShape/hasProcess/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-Filtration', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class ChlorinationStage(_BASE.ChlorinationUnit):
    'Chlorination Stage configuration defined by the seawater RO shapes.'
    _spec_has_process = _PropertySpec(
        name='has_process',
        predicate='https://watermetadata.org/ontology/watr#hasProcess',
        kind='class',
        label='has process',
        definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
        ranges=('Process',),
        range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
        sources=('bc09fac0c70bc9398630ec2a2', 'https://watermetadata.org/ontology/watr#hasProcess', 'https://watermetadata.org/plumb/seawater-ro#ChlorinationStageShape/hasProcess/0'),
        min_count=1,
        required=True,
    )
    has_process: _Rel[type[_BASE.Process]] = _Rel(_spec_has_process)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#ChlorinationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Chlorination Stage',
        definition='Chlorination Stage configuration defined by the seawater RO shapes.',
        properties=(_spec_has_process,),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, https://watermetadata.org/ontology/watr#hasProcess, https://watermetadata.org/plumb/seawater-ro#ChlorinationStageShape/hasProcess/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-Chlorination', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class CoagulationStage(_BASE.CoagulationBasin):
    'Coagulation Stage configuration defined by the seawater RO shapes.'
    _spec_has_process = _PropertySpec(
        name='has_process',
        predicate='https://watermetadata.org/ontology/watr#hasProcess',
        kind='class',
        label='has process',
        definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
        ranges=('Process',),
        range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
        sources=('bc09fac0c70bc9398630ec2a2', 'https://watermetadata.org/ontology/watr#hasProcess', 'https://watermetadata.org/plumb/seawater-ro#CoagulationStageShape/hasProcess/0'),
        min_count=1,
        required=True,
    )
    has_process: _Rel[type[_BASE.Process]] = _Rel(_spec_has_process)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#CoagulationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Coagulation Stage',
        definition='Coagulation Stage configuration defined by the seawater RO shapes.',
        properties=(_spec_has_process,),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, https://watermetadata.org/ontology/watr#hasProcess, https://watermetadata.org/plumb/seawater-ro#CoagulationStageShape/hasProcess/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-Coagulation', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class DosingStage(_BASE.Reactor):
    'Dosing Stage configuration defined by the seawater RO shapes.'
    _spec_has_process = _PropertySpec(
        name='has_process',
        predicate='https://watermetadata.org/ontology/watr#hasProcess',
        kind='class',
        label='has process',
        definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
        ranges=('Process',),
        range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
        sources=('bc09fac0c70bc9398630ec2a2', 'https://watermetadata.org/ontology/watr#hasProcess', 'https://watermetadata.org/plumb/seawater-ro#DosingStageShape/hasProcess/0'),
        min_count=1,
        required=True,
    )
    has_process: _Rel[type[_BASE.Process]] = _Rel(_spec_has_process)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#DosingStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Dosing Stage',
        definition='Dosing Stage configuration defined by the seawater RO shapes.',
        properties=(_spec_has_process,),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, https://watermetadata.org/ontology/watr#hasProcess, https://watermetadata.org/plumb/seawater-ro#DosingStageShape/hasProcess/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-Dosing', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class EnergyRecoveryExchanger(_BASE.PressureExchanger):
    'Energy Recovery Exchanger configuration defined by the seawater RO shapes.'
    _spec_has_property = _PropertySpec(
        name='has_property',
        predicate='http://data.ashrae.org/standard223#hasProperty',
        kind='object',
        label='has property',
        definition='A `Relation` that associates a `Concept` with a `Property`.',
        ranges=('Property',),
        range_groups=(('http://data.ashrae.org/standard223#Property',),),
        sources=('b894486338780f2f7730cd6ec', 'https://watermetadata.org/plumb/seawater-ro#PressureExchangerDesignShape/hasProperty/0'),
    )
    has_property: _Rel[_DEP0.Property] = _Rel(_spec_has_property)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#EnergyRecoveryExchanger',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Energy Recovery Exchanger',
        definition='Energy Recovery Exchanger configuration defined by the seawater RO shapes.',
        properties=(_spec_has_property,),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class FeedSplitter(_DEP0.Junction):
    'Feed Splitter configuration defined by the seawater RO shapes.'
    _spec_medium = _PropertySpec(
        name='medium',
        predicate='http://data.ashrae.org/standard223#hasMedium',
        kind='enum',
        label='has medium',
        definition='The relation `hasMedium` is used to indicate what medium is flowing through the connection (e.g., air, water, electricity). The possible values are defined in `Substance-Medium` (see {s223:Substance-Medium}).',
        range_groups=(('http://data.ashrae.org/standard223#Substance-Medium',),),
        sources=('b27687f66cec843f6f6442183', 'b42897a1302c66ef48c1eb917', 'b668405d00cb3041e9cb292d8', 'b7b6e8b6b692e00280f1836e8', 'b7fcb9534d9769671e8d0b97b', 'b8f0b12dc85f638024437a859', 'b9d6fe703e1f82459a5b8d55b', 'bbbcaeeb178444c2f6593093a', 'bc423102e47022f8fab24adb1', 'be65b6ced07bb4a44f718e9a4', 'bfa6b8152ca8e9eed314182a5', 'bfb8077af53aae66ed43f4c36', 'https://watermetadata.org/plumb/seawater-ro#FeedSplitterShape/hasMedium/0'),
        min_count=1,
        enum_ranges=('http://data.ashrae.org/standard223#Substance-Medium',),
        required=True,
        max_count=1,
    )
    medium: _EnumOne[_EnumValue] = _EnumOne(_spec_medium)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#FeedSplitter',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Feed Splitter',
        definition='Feed Splitter configuration defined by the seawater RO shapes.',
        properties=(_spec_medium,),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='pressure_exchanger', label='pressure_exchanger'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='pump', label='pump'),),
    )
    _shape_constraints = (
        _ShapeValues('has_connection_point', 'b8ad8d8b7d7a41f55c0bc4138, be2099568566b78227dcced58', required=(), defaults=(), choices=None, minimum=2, maximum=None),
        _ShapeValues('medium', 'b27687f66cec843f6f6442183, b42897a1302c66ef48c1eb917, b668405d00cb3041e9cb292d8, b7b6e8b6b692e00280f1836e8, b7fcb9534d9769671e8d0b97b, b8f0b12dc85f638024437a859, b9d6fe703e1f82459a5b8d55b, bbbcaeeb178444c2f6593093a, bc423102e47022f8fab24adb1, be65b6ced07bb4a44f718e9a4, bfa6b8152ca8e9eed314182a5, bfb8077af53aae66ed43f4c36, https://watermetadata.org/plumb/seawater-ro#FeedSplitterShape/hasMedium/0', required=(_TermValue('http://data.ashrae.org/standard223#Fluid-Water', types=()),), defaults=(), choices=None, minimum=1, maximum=1),
    )
    _shape_max_ports = 3
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='inlet')
    pressure_exchanger = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='pressure_exchanger')
    pump = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='pump')
    _point_declarations = {
        'inlet': inlet,
        'pressure_exchanger': pressure_exchanger,
        'pump': pump,
    }
    def __init__(self, name: str | None = None, *,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        medium: _EnumValue | None = None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'cnx': cnx,
            'connected': connected,
            'connected_from': connected_from,
            'connected_through': connected_through,
            'connected_to': connected_to,
            'has_connection_point': has_connection_point,
            'has_optional_connection_point': has_optional_connection_point,
            'has_property': has_property,
            'medium': medium,
        })

class HighPressurePump(_BASE.Pump):
    'High Pressure Pump configuration defined by the seawater RO shapes.'
    _spec_has_property = _PropertySpec(
        name='has_property',
        predicate='http://data.ashrae.org/standard223#hasProperty',
        kind='object',
        label='has property',
        definition='A `Relation` that associates a `Concept` with a `Property`.',
        ranges=('Property',),
        range_groups=(('http://data.ashrae.org/standard223#Property',),),
        sources=('b894486338780f2f7730cd6ec', 'https://watermetadata.org/plumb/seawater-ro#HighPressurePumpDesignShape/hasProperty/0', 'https://watermetadata.org/plumb/seawater-ro#HighPressurePumpDesignShape/hasProperty/1'),
    )
    has_property: _Rel[_DEP0.Property] = _Rel(_spec_has_property)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#HighPressurePump',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='High Pressure Pump',
        definition='High Pressure Pump configuration defined by the seawater RO shapes.',
        properties=(_spec_has_property,),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class IntakePump(_BASE.Pump):
    'Intake Pump configuration defined by the seawater RO shapes.'
    _spec_has_role = _PropertySpec(
        name='has_role',
        predicate='http://data.ashrae.org/standard223#hasRole',
        kind='enum',
        label='has role',
        definition='A `Relation` that associates a role with of a piece of `Equipment`, a `Connection`, `ConnectionPoint`, or `System` within a building (e.g., a heating coil might be associated with `Role-Heating`). Possible values are defined in `EnumerationKind-Role` (see {s223:EnumerationKind-Role}).',
        range_groups=(('http://data.ashrae.org/standard223#EnumerationKind-Role',),),
        sources=('be7260e57dcb51463c8fc48d4', 'https://watermetadata.org/plumb/seawater-ro#IntakePumpShape/hasRole/0'),
        enum_ranges=('http://data.ashrae.org/standard223#EnumerationKind-Role',),
    )
    has_role: _EnumSet[_EnumValue] = _EnumSet(_spec_has_role)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#IntakePump',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Intake Pump',
        definition='Intake Pump configuration defined by the seawater RO shapes.',
        properties=(_spec_has_role,),
    )
    _shape_constraints = (
        _ShapeValues('has_role', 'be7260e57dcb51463c8fc48d4, https://watermetadata.org/plumb/seawater-ro#IntakePumpShape/hasRole/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Role-Feed', types=()),), defaults=(), choices=None, minimum=0, maximum=None),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class Landfill(_BASE.Equipment):
    'Landfill configuration defined by the seawater RO shapes.'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#Landfill',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Landfill',
        definition='Landfill configuration defined by the seawater RO shapes.',
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='https://watermetadata.org/ontology/watr#Fluid-Sludge', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='https://watermetadata.org/ontology/watr#Fluid-Sludge', min_count=1, max_count=1, name='outlet', label='outlet'),),
    )
    _shape_max_ports = 2
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('https://watermetadata.org/ontology/watr#Fluid-Sludge'), direction='in', label='inlet')
    outlet = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('https://watermetadata.org/ontology/watr#Fluid-Sludge'), direction='out', label='outlet')
    _point_declarations = {
        'inlet': inlet,
        'outlet': outlet,
    }
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class MediaFilter(_BASE.UnitProcess):
    'Media Filter configuration defined by the seawater RO shapes.'
    _spec_has_process = _PropertySpec(
        name='has_process',
        predicate='https://watermetadata.org/ontology/watr#hasProcess',
        kind='class',
        label='has process',
        definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
        ranges=('Process',),
        range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
        sources=('bc09fac0c70bc9398630ec2a2', 'https://watermetadata.org/ontology/watr#hasProcess', 'https://watermetadata.org/plumb/seawater-ro#MediaFilterShape/hasProcess/0'),
        min_count=1,
        required=True,
    )
    has_process: _Rel[type[_BASE.Process]] = _Rel(_spec_has_process)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#MediaFilter',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Media Filter',
        definition='Media Filter configuration defined by the seawater RO shapes.',
        properties=(_spec_has_process,),
        cp_slots=(_CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='backwash', label='backwash'), _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='product', label='product'),),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, https://watermetadata.org/ontology/watr#hasProcess, https://watermetadata.org/plumb/seawater-ro#MediaFilterShape/hasProcess/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-MediaFiltration', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
    )
    _shape_max_ports = 3
    backwash = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='backwash')
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='inlet')
    product = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='product')
    _point_declarations = {
        'backwash': backwash,
        'inlet': inlet,
        'product': product,
    }
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class MediaFiltrationStage(_BASE.UnitProcess):
    'Media Filtration Stage configuration defined by the seawater RO shapes.'
    _spec_has_process = _PropertySpec(
        name='has_process',
        predicate='https://watermetadata.org/ontology/watr#hasProcess',
        kind='class',
        label='has process',
        definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
        ranges=('Process',),
        range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
        sources=('bc09fac0c70bc9398630ec2a2', 'https://watermetadata.org/ontology/watr#hasProcess', 'https://watermetadata.org/plumb/seawater-ro#MediaFiltrationStageShape/hasProcess/0'),
        min_count=1,
        required=True,
    )
    has_process: _Rel[type[_BASE.Process]] = _Rel(_spec_has_process)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#MediaFiltrationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Media Filtration Stage',
        definition='Media Filtration Stage configuration defined by the seawater RO shapes.',
        properties=(_spec_has_process,),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, https://watermetadata.org/ontology/watr#hasProcess, https://watermetadata.org/plumb/seawater-ro#MediaFiltrationStageShape/hasProcess/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-MediaFiltration', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class MixingStage(_BASE.StaticMixer):
    'Mixing Stage configuration defined by the seawater RO shapes.'
    _spec_has_process = _PropertySpec(
        name='has_process',
        predicate='https://watermetadata.org/ontology/watr#hasProcess',
        kind='class',
        label='has process',
        definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
        ranges=('Process',),
        range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
        sources=('bc09fac0c70bc9398630ec2a2', 'https://watermetadata.org/ontology/watr#hasProcess', 'https://watermetadata.org/plumb/seawater-ro#MixingStageShape/hasProcess/0'),
        min_count=1,
        required=True,
    )
    has_process: _Rel[type[_BASE.Process]] = _Rel(_spec_has_process)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#MixingStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Mixing Stage',
        definition='Mixing Stage configuration defined by the seawater RO shapes.',
        properties=(_spec_has_process,),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, https://watermetadata.org/ontology/watr#hasProcess, https://watermetadata.org/plumb/seawater-ro#MixingStageShape/hasProcess/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-Mixing', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class PermeateConnection(_DEP0.Pipe):
    'Permeate Connection configuration defined by the seawater RO shapes.'
    _spec_has_property = _PropertySpec(
        name='has_property',
        predicate='http://data.ashrae.org/standard223#hasProperty',
        kind='object',
        label='has property',
        definition='A `Relation` that associates a `Concept` with a `Property`.',
        ranges=('Property',),
        range_groups=(('http://data.ashrae.org/standard223#Property',),),
        sources=('b894486338780f2f7730cd6ec', 'https://watermetadata.org/plumb/seawater-ro#PermeateStateShape/hasProperty/0'),
    )
    has_property: _Rel[_DEP0.Property] = _Rel(_spec_has_property)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#PermeateConnection',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Permeate Connection',
        definition='Permeate Connection configuration defined by the seawater RO shapes.',
        properties=(_spec_has_property,),
    )
    _shape_constraints = (
        _ShapeValues('connects_at', 'bcc0554fe27774b293d04f8f7', required=(), defaults=(), choices=None, minimum=2, maximum=None),
        _ShapeValues('has_thermodynamic_phase', 'beb8f86d7a6cb7b66f442c436', required=(), defaults=(), choices=None, minimum=0, maximum=1),
        _ShapeValues('medium', 'b0131760cbc6e8f22d742dde8, b08013af0fa22636fac5ed53d, b123223c5e01ff28447b865ff, b191b216459fa4b5f132d1672, b27687f66cec843f6f6442183, b44e2ba9901fa7038c51721ff, b59c7af6a2db2bd70f0dac26a, b6af3bcb21b82b70deae5e465, b7fcb9534d9769671e8d0b97b, b8f0b12dc85f638024437a859, bb21b41d9f4b8b32f5821a889, bfa6b8152ca8e9eed314182a5', required=(), defaults=(), choices=None, minimum=1, maximum=1),
    )
    def __init__(self, name: str | None = None, *,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connects_at: _Iterable[_DEP0.ConnectionPoint] | None,
        connects_from: _Iterable[_DEP0.Connectable] | None = None,
        connects_to: _Iterable[_DEP0.Connectable] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_thermodynamic_phase: _EnumValue | None = None,
        medium: _EnumValue | None,
        label: str | None = None, comment: str | None = None, model: _Model | None = None) -> None:
        _Entity.__init__(self, name, label=label, comment=comment, model=model, **{
            'cnx': cnx,
            'connects_at': connects_at,
            'connects_from': connects_from,
            'connects_to': connects_to,
            'has_property': has_property,
            'has_role': has_role,
            'has_thermodynamic_phase': has_thermodynamic_phase,
            'medium': medium,
        })

class ROFeedMixer(_BASE.StaticMixer):
    'ROFeed Mixer configuration defined by the seawater RO shapes.'
    _spec_has_process = _PropertySpec(
        name='has_process',
        predicate='https://watermetadata.org/ontology/watr#hasProcess',
        kind='class',
        label='has process',
        definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
        ranges=('Process',),
        range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
        sources=('bc09fac0c70bc9398630ec2a2', 'https://watermetadata.org/ontology/watr#hasProcess', 'https://watermetadata.org/plumb/seawater-ro#ROFeedMixerShape/hasProcess/0'),
        min_count=1,
        required=True,
    )
    has_process: _Rel[type[_BASE.Process]] = _Rel(_spec_has_process)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#ROFeedMixer',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='ROFeed Mixer',
        definition='ROFeed Mixer configuration defined by the seawater RO shapes.',
        properties=(_spec_has_process,),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='booster', label='booster'), _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='high_pressure', label='high_pressure'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='outlet', label='outlet'),),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, https://watermetadata.org/ontology/watr#hasProcess, https://watermetadata.org/plumb/seawater-ro#ROFeedMixerShape/hasProcess/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-Mixing', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
    )
    _shape_max_ports = 3
    booster = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='booster')
    high_pressure = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='high_pressure')
    outlet = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='outlet')
    _point_declarations = {
        'booster': booster,
        'high_pressure': high_pressure,
        'outlet': outlet,
    }
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class ROStage(_BASE.ReverseOsmosisMembrane):
    'ROStage configuration defined by the seawater RO shapes.'
    _spec_has_process = _PropertySpec(
        name='has_process',
        predicate='https://watermetadata.org/ontology/watr#hasProcess',
        kind='class',
        label='has process',
        definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
        ranges=('Process',),
        range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
        sources=('bc09fac0c70bc9398630ec2a2', 'https://watermetadata.org/ontology/watr#hasProcess', 'https://watermetadata.org/plumb/seawater-ro#ROStageShape/hasProcess/0'),
        min_count=1,
        required=True,
    )
    has_process: _Rel[type[_BASE.Process]] = _Rel(_spec_has_process)
    _spec_has_property = _PropertySpec(
        name='has_property',
        predicate='http://data.ashrae.org/standard223#hasProperty',
        kind='object',
        label='has property',
        definition='A `Relation` that associates a `Concept` with a `Property`.',
        ranges=('Property',),
        range_groups=(('http://data.ashrae.org/standard223#Property',),),
        sources=('b894486338780f2f7730cd6ec', 'https://watermetadata.org/plumb/seawater-ro#MembraneDesignShape/hasProperty/0', 'https://watermetadata.org/plumb/seawater-ro#MembraneDesignShape/hasProperty/1', 'https://watermetadata.org/plumb/seawater-ro#MembraneDesignShape/hasProperty/2', 'https://watermetadata.org/plumb/seawater-ro#MembraneDesignShape/hasProperty/3', 'https://watermetadata.org/plumb/seawater-ro#MembraneDesignShape/hasProperty/4'),
    )
    has_property: _Rel[_DEP0.Property] = _Rel(_spec_has_property)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#ROStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='ROStage',
        definition='ROStage configuration defined by the seawater RO shapes.',
        properties=(_spec_has_process, _spec_has_property,),
        cp_slots=(_CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='concentrate', label='concentrate'), _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='permeate', label='permeate'),),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, https://watermetadata.org/ontology/watr#hasProcess, https://watermetadata.org/plumb/seawater-ro#ROStageShape/hasProcess/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-ReverseOsmosis', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
    )
    _shape_max_ports = 3
    concentrate = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='concentrate')
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='inlet')
    permeate = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='permeate')
    _point_declarations = {
        'concentrate': concentrate,
        'inlet': inlet,
        'permeate': permeate,
    }
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class SeawaterFeed(_BASE.Equipment):
    'Seawater Feed configuration defined by the seawater RO shapes.'
    _spec_has_role = _PropertySpec(
        name='has_role',
        predicate='http://data.ashrae.org/standard223#hasRole',
        kind='enum',
        label='has role',
        definition='A `Relation` that associates a role with of a piece of `Equipment`, a `Connection`, `ConnectionPoint`, or `System` within a building (e.g., a heating coil might be associated with `Role-Heating`). Possible values are defined in `EnumerationKind-Role` (see {s223:EnumerationKind-Role}).',
        range_groups=(('http://data.ashrae.org/standard223#EnumerationKind-Role',),),
        sources=('be7260e57dcb51463c8fc48d4', 'https://watermetadata.org/plumb/seawater-ro#SeawaterFeedShape/hasRole/0'),
        enum_ranges=('http://data.ashrae.org/standard223#EnumerationKind-Role',),
    )
    has_role: _EnumSet[_EnumValue] = _EnumSet(_spec_has_role)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#SeawaterFeed',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Seawater Feed',
        definition='Seawater Feed configuration defined by the seawater RO shapes.',
        properties=(_spec_has_role,),
        cp_slots=(_CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='outlet', label='outlet'),),
    )
    _shape_constraints = (
        _ShapeValues('has_role', 'be7260e57dcb51463c8fc48d4, https://watermetadata.org/plumb/seawater-ro#SeawaterFeedShape/hasRole/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Role-Feed', types=()),), defaults=(), choices=None, minimum=0, maximum=None),
    )
    _shape_max_ports = 1
    outlet = _PointDeclaration[_PointRef](count=1, medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='outlet')
    _point_declarations = {
        'outlet': outlet,
    }
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

class StorageTank(_BASE.Tank):
    'Storage Tank configuration defined by the seawater RO shapes.'
    _spec_has_property = _PropertySpec(
        name='has_property',
        predicate='http://data.ashrae.org/standard223#hasProperty',
        kind='object',
        label='has property',
        definition='A `Relation` that associates a `Concept` with a `Property`.',
        ranges=('Property',),
        range_groups=(('http://data.ashrae.org/standard223#Property',),),
        sources=('b894486338780f2f7730cd6ec', 'https://watermetadata.org/plumb/seawater-ro#ResidenceTimeDesignShape/hasProperty/0'),
    )
    has_property: _Rel[_DEP0.Property] = _Rel(_spec_has_property)
    _spec_has_role = _PropertySpec(
        name='has_role',
        predicate='http://data.ashrae.org/standard223#hasRole',
        kind='enum',
        label='has role',
        definition='A `Relation` that associates a role with of a piece of `Equipment`, a `Connection`, `ConnectionPoint`, or `System` within a building (e.g., a heating coil might be associated with `Role-Heating`). Possible values are defined in `EnumerationKind-Role` (see {s223:EnumerationKind-Role}).',
        range_groups=(('http://data.ashrae.org/standard223#EnumerationKind-Role',),),
        sources=('be7260e57dcb51463c8fc48d4', 'https://watermetadata.org/plumb/seawater-ro#StorageTankShape/hasRole/0'),
        enum_ranges=('http://data.ashrae.org/standard223#EnumerationKind-Role',),
    )
    has_role: _EnumSet[_EnumValue] = _EnumSet(_spec_has_role)
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/seawater-ro#StorageTank',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Storage Tank',
        definition='Storage Tank configuration defined by the seawater RO shapes.',
        properties=(_spec_has_property, _spec_has_role,),
    )
    _shape_constraints = (
        _ShapeValues('has_role', 'be7260e57dcb51463c8fc48d4, https://watermetadata.org/plumb/seawater-ro#StorageTankShape/hasRole/0', required=(_TermValue('https://watermetadata.org/ontology/watr#Role-Storage', types=()),), defaults=(), choices=None, minimum=0, maximum=None),
    )
    def __init__(self, name: str | None = None, *,
        actuated_by_property: _Iterable[_DEP0.ActuatableProperty] | None = None,
        cnx: _Iterable[_DEP0.ConnectionPoint] | None = None,
        connected: _Iterable[_DEP0.Connectable] | None = None,
        connected_from: _Iterable[_DEP0.Connectable] | None = None,
        connected_through: _Iterable[_DEP0.Connection] | None = None,
        connected_to: _Iterable[_DEP0.Connectable] | None = None,
        contains_: _Iterable[_DEP0.Equipment | _DEP0.Junction] | None = None,
        executes: _Iterable[_DEP0.Function] | None = None,
        has_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_optional_connection_point: _Iterable[_DEP0.ConnectionPoint] | None = None,
        has_physical_location: _Iterable[_DEP0.PhysicalSpace] | None = None,
        has_process: _Iterable[type[_BASE.Process]] | None = None,
        has_property: _Iterable[_DEP0.Property] | None = None,
        has_role: _Iterable[_EnumValue] | None = None,
        has_treatment_objective: _Iterable[type[_BASE.TreatmentObjective]] | None = None,
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
            'has_process': has_process,
            'has_property': has_property,
            'has_role': has_role,
            'has_treatment_objective': has_treatment_objective,
            'medium': medium,
        })

@_dataclass(frozen=True, kw_only=True)
class HighPressurePumpDesign(_PropertySchema):
    'HighPressurePumpDesign quantities with nominal aspects and shape-declared default units.'
    source_shape = 'https://watermetadata.org/plumb/seawater-ro#HighPressurePumpDesignShape'
    _definitions = (
        _QuantityDefinition(name='efficiency', source_shape='https://watermetadata.org/plumb/seawater-ro#HighPressurePumpDesign_efficiencyShape', kind=_kinds.Efficiency, unit=_units.UNITLESS, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Pump efficiency', allowed_units=(_units.UNITLESS,), description=None, notation=None, local_name='efficiency', minimum=0.0, maximum=1.0, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
        _QuantityDefinition(name='operating_pressure', source_shape='https://watermetadata.org/plumb/seawater-ro#HighPressurePumpDesign_operating_pressureShape', kind=_kinds.Pressure, unit=_units.PA, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Operating pressure', allowed_units=(_units.PA, _units.KiloPA, _units.BAR, _units.PSI,), description=None, notation=None, local_name='operating-pressure', minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
    )
    efficiency: float | _QuantityAmount
    'Pump efficiency; ; default unit http://qudt.org/vocab/unit/UNITLESS; source https://watermetadata.org/plumb/seawater-ro#HighPressurePumpDesign_efficiencyShape'
    operating_pressure: float | _QuantityAmount
    'Operating pressure; ; default unit http://qudt.org/vocab/unit/PA; source https://watermetadata.org/plumb/seawater-ro#HighPressurePumpDesign_operating_pressureShape'

@_dataclass(frozen=True, kw_only=True)
class MembraneDesign(_PropertySchema):
    'MembraneDesign quantities with nominal aspects and shape-declared default units.'
    source_shape = 'https://watermetadata.org/plumb/seawater-ro#MembraneDesignShape'
    _definitions = (
        _QuantityDefinition(name='membrane_area', source_shape='https://watermetadata.org/plumb/seawater-ro#MembraneDesign_membrane_areaShape', kind=_kinds.Area, unit=_units.M2, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Membrane area', allowed_units=(_units.M2, _units.FT2,), description=None, notation=None, local_name='membrane-area', minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
        _QuantityDefinition(name='spacer_porosity', source_shape='https://watermetadata.org/plumb/seawater-ro#MembraneDesign_spacer_porosityShape', kind=_kinds.DimensionlessRatio, unit=_units.UNITLESS, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Feed spacer porosity', allowed_units=(_units.UNITLESS,), description=None, notation=None, local_name='spacer-porosity', minimum=0.0, maximum=1.0, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
        _QuantityDefinition(name='channel_height', source_shape='https://watermetadata.org/plumb/seawater-ro#MembraneDesign_channel_heightShape', kind=_kinds.Length, unit=_units.M, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Membrane channel height', allowed_units=(_units.M, _units.FT, _units.CentiM, _units.MilliM,), description=None, notation=None, local_name='channel-height', minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
        _QuantityDefinition(name='stage_width', source_shape='https://watermetadata.org/plumb/seawater-ro#MembraneDesign_stage_widthShape', kind=_kinds.Length, unit=_units.M, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Membrane width per stage', allowed_units=(_units.M, _units.FT, _units.CentiM, _units.MilliM,), description=None, notation=None, local_name='stage-width', minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
        _QuantityDefinition(name='salt_permeability', source_shape='https://watermetadata.org/plumb/seawater-ro#MembraneDesign_salt_permeabilityShape', kind=_kinds.Velocity, unit=_units.M_PER_SEC, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Salt permeability coefficient', allowed_units=(_units.M_PER_SEC, _units.FT_PER_SEC,), description=None, notation=None, local_name='salt-permeability', minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
    )
    membrane_area: float | _QuantityAmount
    'Membrane area; ; default unit http://qudt.org/vocab/unit/M2; source https://watermetadata.org/plumb/seawater-ro#MembraneDesign_membrane_areaShape'
    spacer_porosity: float | _QuantityAmount
    'Feed spacer porosity; ; default unit http://qudt.org/vocab/unit/UNITLESS; source https://watermetadata.org/plumb/seawater-ro#MembraneDesign_spacer_porosityShape'
    channel_height: float | _QuantityAmount
    'Membrane channel height; ; default unit http://qudt.org/vocab/unit/M; source https://watermetadata.org/plumb/seawater-ro#MembraneDesign_channel_heightShape'
    stage_width: float | _QuantityAmount
    'Membrane width per stage; ; default unit http://qudt.org/vocab/unit/M; source https://watermetadata.org/plumb/seawater-ro#MembraneDesign_stage_widthShape'
    salt_permeability: float | _QuantityAmount
    'Salt permeability coefficient; ; default unit http://qudt.org/vocab/unit/M-PER-SEC; source https://watermetadata.org/plumb/seawater-ro#MembraneDesign_salt_permeabilityShape'

@_dataclass(frozen=True, kw_only=True)
class PermeateState(_PropertySchema):
    'PermeateState quantities with nominal aspects and shape-declared default units.'
    source_shape = 'https://watermetadata.org/plumb/seawater-ro#PermeateStateShape'
    _definitions = (
        _QuantityDefinition(name='pressure', source_shape='https://watermetadata.org/plumb/seawater-ro#PermeateState_pressureShape', kind=_kinds.Pressure, unit=_units.PA, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Nominal permeate-side pressure', allowed_units=(_units.PA, _units.KiloPA, _units.BAR, _units.PSI,), description=None, notation=None, local_name='side-pressure', minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
    )
    pressure: float | _QuantityAmount
    'Nominal permeate-side pressure; ; default unit http://qudt.org/vocab/unit/PA; source https://watermetadata.org/plumb/seawater-ro#PermeateState_pressureShape'

@_dataclass(frozen=True, kw_only=True)
class PressureExchangerDesign(_PropertySchema):
    'PressureExchangerDesign quantities with nominal aspects and shape-declared default units.'
    source_shape = 'https://watermetadata.org/plumb/seawater-ro#PressureExchangerDesignShape'
    _definitions = (
        _QuantityDefinition(name='efficiency', source_shape='https://watermetadata.org/plumb/seawater-ro#PressureExchangerDesign_efficiencyShape', kind=_kinds.Efficiency, unit=_units.UNITLESS, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Pressure-exchanger efficiency', allowed_units=(_units.UNITLESS,), description=None, notation=None, local_name='efficiency', minimum=0.0, maximum=1.0, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
    )
    efficiency: float | _QuantityAmount
    'Pressure-exchanger efficiency; ; default unit http://qudt.org/vocab/unit/UNITLESS; source https://watermetadata.org/plumb/seawater-ro#PressureExchangerDesign_efficiencyShape'

@_dataclass(frozen=True, kw_only=True)
class PumpDesign(_PropertySchema):
    'PumpDesign quantities with nominal aspects and shape-declared default units.'
    source_shape = 'https://watermetadata.org/plumb/seawater-ro#PumpDesignShape'
    _definitions = (
        _QuantityDefinition(name='efficiency', source_shape='https://watermetadata.org/plumb/seawater-ro#PumpDesign_efficiencyShape', kind=_kinds.Efficiency, unit=_units.UNITLESS, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Pump efficiency', allowed_units=(_units.UNITLESS,), description=None, notation=None, local_name='efficiency', minimum=0.0, maximum=1.0, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
    )
    efficiency: float | _QuantityAmount
    'Pump efficiency; ; default unit http://qudt.org/vocab/unit/UNITLESS; source https://watermetadata.org/plumb/seawater-ro#PumpDesign_efficiencyShape'

@_dataclass(frozen=True, kw_only=True)
class ResidenceTimeDesign(_PropertySchema):
    'ResidenceTimeDesign quantities with nominal aspects and shape-declared default units.'
    source_shape = 'https://watermetadata.org/plumb/seawater-ro#ResidenceTimeDesignShape'
    _definitions = (
        _QuantityDefinition(name='residence_time', source_shape='https://watermetadata.org/plumb/seawater-ro#ResidenceTimeDesign_residence_timeShape', kind=_kinds.Time, unit=_units.HR, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Nominal residence time', allowed_units=(_units.HR, _units.SEC, _units.MIN,), description=None, notation=None, local_name='residence-time', minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
    )
    residence_time: float | _QuantityAmount
    'Nominal residence time; ; default unit http://qudt.org/vocab/unit/HR; source https://watermetadata.org/plumb/seawater-ro#ResidenceTimeDesign_residence_timeShape'

@_dataclass(frozen=True, kw_only=True)
class SeawaterFeedState(_PropertySchema):
    'SeawaterFeedState quantities with nominal aspects and shape-declared default units.'
    source_shape = 'https://watermetadata.org/plumb/seawater-ro#SeawaterFeedStateShape'
    _definitions = (
        _QuantityDefinition(name='flow_rate', source_shape='https://watermetadata.org/plumb/seawater-ro#SeawaterFeedState_flow_rateShape', kind=_kinds.VolumeFlowRate, unit=_units.GAL_US_PER_DAY, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Influent flow rate', allowed_units=(_units.GAL_US_PER_DAY, _units.M3_PER_DAY, _units.L_PER_SEC, _units.M3_PER_SEC,), description=None, notation=None, local_name='flow-rate', minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), of_medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), properties=()),
        _QuantityDefinition(name='total_dissolved_solids', source_shape='https://watermetadata.org/plumb/seawater-ro#SeawaterFeedState_total_dissolved_solidsShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_L, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Influent total dissolved solids concentration', allowed_units=(_units.GM_PER_L, _units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L,), description=None, notation=None, local_name='tds-concentration', minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), of_medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), of_substance=_BASE.REGISTRY.resolve_enum('https://watermetadata.org/ontology/watr#Constituent-Salt'), properties=()),
        _QuantityDefinition(name='total_suspended_solids', source_shape='https://watermetadata.org/plumb/seawater-ro#SeawaterFeedState_total_suspended_solidsShape', kind=_kinds.MassConcentration, unit=_units.GM_PER_L, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Influent total suspended solids concentration', allowed_units=(_units.GM_PER_L, _units.GM_PER_M3, _units.KiloGM_PER_M3, _units.MilliGM_PER_L,), description=None, notation=None, local_name='tss-concentration', minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), of_medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), of_substance=_BASE.REGISTRY.resolve_enum('https://watermetadata.org/ontology/watr#Constituent-SuspendedSolids'), properties=()),
        _QuantityDefinition(name='temperature', source_shape='https://watermetadata.org/plumb/seawater-ro#SeawaterFeedState_temperatureShape', kind=_kinds.Temperature, unit=_units.K, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Influent temperature', allowed_units=(_units.K, _units.DEG_C,), description=None, notation=None, local_name='temperature', minimum=None, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), of_medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), properties=()),
        _QuantityDefinition(name='pressure', source_shape='https://watermetadata.org/plumb/seawater-ro#SeawaterFeedState_pressureShape', kind=_kinds.Pressure, unit=_units.PA, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Influent pressure', allowed_units=(_units.PA, _units.KiloPA, _units.BAR, _units.PSI,), description=None, notation=None, local_name='pressure', minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), of_medium=_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), properties=()),
    )
    flow_rate: float | _QuantityAmount
    'Influent flow rate; ; default unit http://qudt.org/vocab/unit/GAL_US-PER-DAY; source https://watermetadata.org/plumb/seawater-ro#SeawaterFeedState_flow_rateShape'
    total_dissolved_solids: float | _QuantityAmount
    'Influent total dissolved solids concentration; ; default unit http://qudt.org/vocab/unit/GM-PER-L; source https://watermetadata.org/plumb/seawater-ro#SeawaterFeedState_total_dissolved_solidsShape'
    total_suspended_solids: float | _QuantityAmount
    'Influent total suspended solids concentration; ; default unit http://qudt.org/vocab/unit/GM-PER-L; source https://watermetadata.org/plumb/seawater-ro#SeawaterFeedState_total_suspended_solidsShape'
    temperature: float | _QuantityAmount
    'Influent temperature; ; default unit http://qudt.org/vocab/unit/K; source https://watermetadata.org/plumb/seawater-ro#SeawaterFeedState_temperatureShape'
    pressure: float | _QuantityAmount
    'Influent pressure; ; default unit http://qudt.org/vocab/unit/PA; source https://watermetadata.org/plumb/seawater-ro#SeawaterFeedState_pressureShape'

@_dataclass(frozen=True, kw_only=True)
class UVDesign(_PropertySchema):
    'UVDesign quantities with nominal aspects and shape-declared default units.'
    source_shape = 'https://watermetadata.org/plumb/seawater-ro#UVDesignShape'
    _definitions = (
        _QuantityDefinition(name='reduction_equivalent_dose', source_shape='https://watermetadata.org/plumb/seawater-ro#UVDesign_reduction_equivalent_doseShape', kind=_kinds.EnergyPerArea, unit=_units.J_PER_CentiM2, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='Reduction-equivalent UV dose', allowed_units=(_units.J_PER_CentiM2, _units.J_PER_M2,), description=None, notation=None, local_name='reduction-equivalent-dose', minimum=0.0, maximum=None, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
        _QuantityDefinition(name='transmittance', source_shape='https://watermetadata.org/plumb/seawater-ro#UVDesign_transmittanceShape', kind=_kinds.Transmittance, unit=_units.UNITLESS, datatype='http://www.w3.org/2001/XMLSchema#double', fixed_unit=False, label='UV transmittance', allowed_units=(_units.UNITLESS,), description=None, notation=None, local_name='transmittance', minimum=0.0, maximum=1.0, allowed_values=(), property_class=_BASE.QuantifiableProperty, aspects=(_BASE.REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Aspect-Nominal'),), properties=()),
    )
    reduction_equivalent_dose: float | _QuantityAmount
    'Reduction-equivalent UV dose; ; default unit http://qudt.org/vocab/unit/J-PER-CentiM2; source https://watermetadata.org/plumb/seawater-ro#UVDesign_reduction_equivalent_doseShape'
    transmittance: float | _QuantityAmount
    'UV transmittance; ; default unit http://qudt.org/vocab/unit/UNITLESS; source https://watermetadata.org/plumb/seawater-ro#UVDesign_transmittanceShape'

__all__ = ['ONTOLOGY', 'REGISTRY', 'AdvancedOxidationStage', 'BackwashSeparator', 'BackwashStage', 'BoosterPump', 'CartridgeFiltrationStage', 'ChlorinationStage', 'CoagulationStage', 'DosingStage', 'EnergyRecoveryExchanger', 'FeedSplitter', 'HighPressurePump', 'IntakePump', 'Landfill', 'MediaFilter', 'MediaFiltrationStage', 'MixingStage', 'PermeateConnection', 'ROFeedMixer', 'ROStage', 'SeawaterFeed', 'StorageTank', 'HighPressurePumpDesign', 'MembraneDesign', 'PermeateState', 'PressureExchangerDesign', 'PumpDesign', 'ResidenceTimeDesign', 'SeawaterFeedState', 'UVDesign']
