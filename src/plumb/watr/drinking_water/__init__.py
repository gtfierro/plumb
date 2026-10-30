"""DrinkingWater: generated from RDF/SHACL. DO NOT EDIT."""
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
ONTOLOGY = _OntologyInfo('DrinkingWater', 'https://watermetadata.org/plumb/drinking-water#', source='ontology/drinking-water.ttl')
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
_REGISTRY.terms_by_iri.update({})

class ChlorinationStage(_BASE.ChlorinationUnit):
    'Chlorine dosing and a contact stage with the objective of disinfection.'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/drinking-water#ChlorinationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Chlorination and contact stage',
        definition='Chlorine dosing and a contact stage with the objective of disinfection.',
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='outlet', label='outlet'),),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'cb12af41702c1ba288b2ea584cf88da18317ab814bb3ccb2f4c0ac463cf27a6da02', required=(_BASE.Process_Chlorination,), defaults=(), choices=(), minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'cb137a260cbcfcac91ed1a981800f20aedbec4428d23987bd6d27e25414069ac49a', required=(_BASE.TreatmentObjective_Disinfection,), defaults=(), choices=(), minimum=0, maximum=None),
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

class ClarificationStage(_BASE.SedimentationTank):
    'Settles flocs and separates clarified water from a sludge withdrawal.'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/drinking-water#ClarificationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Clarification stage',
        definition='Settles flocs and separates clarified water from a sludge withdrawal.',
        properties=(),
        cp_slots=(_CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='clarified_water', label='clarified_water'), _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='https://watermetadata.org/ontology/watr#Fluid-Sludge', min_count=1, max_count=1, name='sludge', label='sludge'),),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'cb13e81b1c87f466d28536cc9d6f11d9aad2144e9578de3d59e3c94c5defab8ced4', required=(_BASE.Process_Settling,), defaults=(), choices=(), minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'cb1556cb4a6cc4ab703282b9b374494717d39be8abc289956e40f483833734f7bf3', required=(_BASE.TreatmentObjective_Clarification,), defaults=(), choices=(), minimum=0, maximum=None),
    )
    _shape_max_ports = 3
    clarified_water = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='clarified_water')
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='inlet')
    sludge = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['https://watermetadata.org/ontology/watr#Fluid-Sludge'], direction='out', label='sludge')
    _point_declarations = {
        'clarified_water': clarified_water,
        'inlet': inlet,
        'sludge': sludge,
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

class CoagulationStage(_BASE.CoagulationBasin):
    'Coagulant addition and particle destabilization ahead of flocculation.'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/drinking-water#CoagulationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Coagulation stage',
        definition='Coagulant addition and particle destabilization ahead of flocculation.',
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='outlet', label='outlet'),),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'cb172c0e033255224fb32955471031954076a4e16527a4ede2a11cc4196e495ac8e', required=(_BASE.Process_Coagulation,), defaults=(), choices=(), minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'cb14be08cca11b578ad72e53d419b982daa7fb5dce47d2ac407e95368bcd49d1610', required=(_BASE.TreatmentObjective_TurbidityRemoval,), defaults=(), choices=(), minimum=0, maximum=None),
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

class FlocculationStage(_BASE.FlocculationBasin):
    'Gentle mixing to form flocs that can settle in the clarifier.'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/drinking-water#FlocculationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Flocculation stage',
        definition='Gentle mixing to form flocs that can settle in the clarifier.',
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='outlet', label='outlet'),),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'cb673a4698bea5cc55d6d1597ab783628d1e847b0697741aaeec137d798e5e948a', required=(_BASE.Process_Flocculation,), defaults=(), choices=(), minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'cb1326af8ed69dab16e7cf90378ac3e8b121b45469b489e8fe9c5a35e71b23f77f3', required=(_BASE.TreatmentObjective_TurbidityRemoval,), defaults=(), choices=(), minimum=0, maximum=None),
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

class RapidSandFiltrationStage(_BASE.RapidSandFilter):
    'Filters clarified water through sand; spent backwash leaves separately during cleaning.'
    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/drinking-water#RapidSandFiltrationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Rapid sand filtration stage',
        definition='Filters clarified water through sand; spent backwash leaves separately during cleaning.',
        properties=(),
        cp_slots=(_CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='backwash_supply', label='backwash_supply'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='backwash_waste', label='backwash_waste'), _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='filtered_water', label='filtered_water'), _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', min_count=1, max_count=1, name='inlet', label='inlet'),),
    )
    _shape_constraints = (
        _ShapeValues('has_process', 'cb1646f6a6b21cab8cbfcf97528ad0560db127964549809ee2057975a54b4bff291', required=(_BASE.Process_RapidSandFiltration,), defaults=(), choices=(), minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'cb1b45607b38c7a00dd4e618c308c6ce9f6a7b7c7f4f442f5efd3b0ad7e0b18c3f5', required=(_BASE.TreatmentObjective_TurbidityRemoval,), defaults=(), choices=(), minimum=0, maximum=None),
    )
    _shape_max_ports = 4
    backwash_supply = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='backwash_supply')
    backwash_waste = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='backwash_waste')
    filtered_water = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='out', label='filtered_water')
    inlet = _PointDeclaration[_PointRef](count=1, medium=_BASE._REGISTRY.enums_by_iri['http://data.ashrae.org/standard223#Fluid-Water'], direction='in', label='inlet')
    _point_declarations = {
        'backwash_supply': backwash_supply,
        'backwash_waste': backwash_waste,
        'filtered_water': filtered_water,
        'inlet': inlet,
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

__all__ = ['ONTOLOGY', 'REGISTRY', 'ChlorinationStage', 'ClarificationStage', 'CoagulationStage', 'FlocculationStage', 'RapidSandFiltrationStage']
