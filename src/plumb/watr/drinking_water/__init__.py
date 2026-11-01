"""DrinkingWater: generated from RDF/SHACL. DO NOT EDIT."""
# ruff: noqa
from __future__ import annotations
from dataclasses import dataclass as _dataclass
from typing import Iterable as _Iterable
import plumb.watr as _BASE
import plumb.s223 as _DEP0
from plumb.core import (Entity as _EntityBase, ClassInfo as _ClassInfo, CPSlot as _CPSlot, CPConstraint as _CPConstraint, provided as _provided,
    Model as _Model, Registry as _Registry, OntologyInfo as _OntologyInfo,
    PropertySpec as _PropertySpec, TermOne as _TermOne, Lit as _Lit, Rel as _Rel, RelOne as _RelOne, EnumOne as _EnumOne, EnumSet as _EnumSet, ValueOne as _ValueOne,
    PropertySchema as _PropertySchema, QuantityDefinition as _QuantityDefinition,
    QuantityAmount as _QuantityAmount, TermValue as _TermValue, EnumValue as _EnumValue, DeferredEndpoint as _DeferredEndpoint)
from plumb.core.points import PointDeclaration as _PointDeclaration, PointRef as _PointRef, PointGroupRef as _PointGroupRef
from plumb.core.shape_constraints import ShapeValues as _ShapeValues
from plumb.qudt import units as _units, quantity_kinds as _kinds
ONTOLOGY = _OntologyInfo('DrinkingWater', 'https://watermetadata.org/plumb/drinking-water#', source='ontology/drinking-water.ttl')
_REGISTRY = _Registry(ONTOLOGY)
REGISTRY = _REGISTRY
_REGISTRY.include(_BASE.REGISTRY)
from pathlib import Path as _Path
from rdflib import Graph as _Graph
if '__file__' in globals():
    _REGISTRY.schema_graph = _Graph().parse(_Path(__file__).with_name('_shapes.ttl'))
_REGISTRY.terms_by_iri.update({})

_P_ChlorinationStage_has_process = _PropertySpec(
    name='has_process',
    predicate='https://watermetadata.org/ontology/watr#hasProcess',
    kind='class',
    label='has process',
    definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
    ranges=('Process',),
    range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
    sources=('bc09fac0c70bc9398630ec2a2', 'cb12af41702c1ba288b2ea584cf88da18317ab814bb3ccb2f4c0ac463cf27a6da02', 'https://watermetadata.org/ontology/watr#hasProcess'),
    min_count=1,
    required=True,
)

_P_ChlorinationStage_has_treatment_objective = _PropertySpec(
    name='has_treatment_objective',
    predicate='https://watermetadata.org/ontology/watr#hasTreatmentObjective',
    kind='class',
    label='has treatment objective',
    definition='Associates a piece of equipment or a system with the treatment objective it is intended to achieve. What it does to achieve that is watr:hasProcess.',
    ranges=('TreatmentObjective',),
    range_groups=(('https://watermetadata.org/ontology/watr#TreatmentObjective',),),
    sources=('cb137a260cbcfcac91ed1a981800f20aedbec4428d23987bd6d27e25414069ac49a', 'https://watermetadata.org/ontology/watr#hasTreatmentObjective'),
)

class ChlorinationStage(_BASE.ChlorinationUnit):
    """Chlorine dosing and a contact stage with the objective of disinfection.

    Ontology: DrinkingWater — https://watermetadata.org/plumb/drinking-water#ChlorinationStage
    """

    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/drinking-water#ChlorinationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Chlorination and contact stage',
        definition='Chlorine dosing and a contact stage with the objective of disinfection.',
        parent_iris=('https://watermetadata.org/ontology/watr#ChlorinationUnit',),
        ancestor_iris=('http://data.ashrae.org/standard223#Concept', 'http://data.ashrae.org/standard223#Connectable', 'http://data.ashrae.org/standard223#Equipment', 'http://www.w3.org/2000/01/rdf-schema#Resource', 'https://watermetadata.org/ontology/watr#ChlorinationUnit', 'https://watermetadata.org/ontology/watr#DisinfectionUnit', 'https://watermetadata.org/ontology/watr#Reactor', 'https://watermetadata.org/ontology/watr#Tank', 'https://watermetadata.org/ontology/watr#UnitProcess'),
        properties=(_P_ChlorinationStage_has_process, _P_ChlorinationStage_has_treatment_objective,),
        cp_slots=(
            _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', medium_options=(), min_count=1, max_count=1, name='inlet', label='inlet'),
            _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', medium_options=(), min_count=1, max_count=1, name='outlet', label='outlet'),
        ),
        class_defaults=(('has_process', 'Process_Chlorination'),),
    )

    has_process: _Rel[type[_BASE.Process]] = _Rel(_P_ChlorinationStage_has_process)
    """Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape. (https://watermetadata.org/ontology/watr#hasProcess)"""

    has_treatment_objective: _Rel[type[_BASE.TreatmentObjective]] = _Rel(_P_ChlorinationStage_has_treatment_objective)
    """Associates a piece of equipment or a system with the treatment objective it is intended to achieve. What it does to achieve that is watr:hasProcess. (https://watermetadata.org/ontology/watr#hasTreatmentObjective)"""
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, cb12af41702c1ba288b2ea584cf88da18317ab814bb3ccb2f4c0ac463cf27a6da02, https://watermetadata.org/ontology/watr#hasProcess', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-Chlorination', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'cb137a260cbcfcac91ed1a981800f20aedbec4428d23987bd6d27e25414069ac49a, https://watermetadata.org/ontology/watr#hasTreatmentObjective', required=(_TermValue('https://watermetadata.org/ontology/watr#TreatmentObjective-Disinfection', types=()),), defaults=(), choices=None, minimum=0, maximum=None),
    )
    _shape_max_ports = 2
    inlet = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='inlet')
    outlet = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='outlet')
    _point_declarations = {
        'inlet': inlet,
        'outlet': outlet,
    }

    def __init__(
        self,
        name: str | None = None,
        *,
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
        label: str | None = None,
        comment: str | None = None,
        model: _Model | None = None,
    ) -> None:
        # Funnel straight to the runtime base: generated __init__ methods are
        # typed sugar, not a cooperative chain (parents' signatures differ).
        _EntityBase.__init__(
            self,
            name,
            label=label,
            comment=comment,
            model=model,
            **_provided(
                actuated_by_property=actuated_by_property,
                cnx=cnx,
                connected=connected,
                connected_from=connected_from,
                connected_through=connected_through,
                connected_to=connected_to,
                contains_=contains_,
                executes=executes,
                has_connection_point=has_connection_point,
                has_optional_connection_point=has_optional_connection_point,
                has_physical_location=has_physical_location,
                has_process=has_process,
                has_property=has_property,
                has_role=has_role,
                has_treatment_objective=has_treatment_objective,
                medium=medium,
            ),
        )

_P_ClarificationStage_has_process = _PropertySpec(
    name='has_process',
    predicate='https://watermetadata.org/ontology/watr#hasProcess',
    kind='class',
    label='has process',
    definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
    ranges=('Process',),
    range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
    sources=('bc09fac0c70bc9398630ec2a2', 'cb13e81b1c87f466d28536cc9d6f11d9aad2144e9578de3d59e3c94c5defab8ced4', 'https://watermetadata.org/ontology/watr#hasProcess'),
    min_count=1,
    required=True,
)

_P_ClarificationStage_has_treatment_objective = _PropertySpec(
    name='has_treatment_objective',
    predicate='https://watermetadata.org/ontology/watr#hasTreatmentObjective',
    kind='class',
    label='has treatment objective',
    definition='Associates a piece of equipment or a system with the treatment objective it is intended to achieve. What it does to achieve that is watr:hasProcess.',
    ranges=('TreatmentObjective',),
    range_groups=(('https://watermetadata.org/ontology/watr#TreatmentObjective',),),
    sources=('cb1556cb4a6cc4ab703282b9b374494717d39be8abc289956e40f483833734f7bf3', 'https://watermetadata.org/ontology/watr#hasTreatmentObjective'),
)

class ClarificationStage(_BASE.SedimentationTank):
    """Settles flocs and separates clarified water from a sludge withdrawal.

    Ontology: DrinkingWater — https://watermetadata.org/plumb/drinking-water#ClarificationStage
    """

    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/drinking-water#ClarificationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Clarification stage',
        definition='Settles flocs and separates clarified water from a sludge withdrawal.',
        parent_iris=('https://watermetadata.org/ontology/watr#SedimentationTank',),
        ancestor_iris=('http://data.ashrae.org/standard223#Concept', 'http://data.ashrae.org/standard223#Connectable', 'http://data.ashrae.org/standard223#Equipment', 'http://www.w3.org/2000/01/rdf-schema#Resource', 'https://watermetadata.org/ontology/watr#SedimentationTank', 'https://watermetadata.org/ontology/watr#SeparationTank', 'https://watermetadata.org/ontology/watr#Tank', 'https://watermetadata.org/ontology/watr#UnitProcess'),
        properties=(_P_ClarificationStage_has_process, _P_ClarificationStage_has_treatment_objective,),
        cp_slots=(
            _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', medium_options=(), min_count=1, max_count=1, name='clarified_water', label='clarified_water'),
            _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', medium_options=(), min_count=1, max_count=1, name='inlet', label='inlet'),
            _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='https://watermetadata.org/ontology/watr#Fluid-Sludge', medium_options=(), min_count=1, max_count=1, name='sludge', label='sludge'),
        ),
        class_defaults=(('has_process', 'Process_Settling'),),
    )

    has_process: _Rel[type[_BASE.Process]] = _Rel(_P_ClarificationStage_has_process)
    """Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape. (https://watermetadata.org/ontology/watr#hasProcess)"""

    has_treatment_objective: _Rel[type[_BASE.TreatmentObjective]] = _Rel(_P_ClarificationStage_has_treatment_objective)
    """Associates a piece of equipment or a system with the treatment objective it is intended to achieve. What it does to achieve that is watr:hasProcess. (https://watermetadata.org/ontology/watr#hasTreatmentObjective)"""
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, cb13e81b1c87f466d28536cc9d6f11d9aad2144e9578de3d59e3c94c5defab8ced4, https://watermetadata.org/ontology/watr#hasProcess', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-Settling', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'cb1556cb4a6cc4ab703282b9b374494717d39be8abc289956e40f483833734f7bf3, https://watermetadata.org/ontology/watr#hasTreatmentObjective', required=(_TermValue('https://watermetadata.org/ontology/watr#TreatmentObjective-Clarification', types=()),), defaults=(), choices=None, minimum=0, maximum=None),
    )
    _shape_max_ports = 3
    clarified_water = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='clarified_water')
    inlet = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='inlet')
    sludge = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('https://watermetadata.org/ontology/watr#Fluid-Sludge'), direction='out', label='sludge')
    _point_declarations = {
        'clarified_water': clarified_water,
        'inlet': inlet,
        'sludge': sludge,
    }

    def __init__(
        self,
        name: str | None = None,
        *,
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
        label: str | None = None,
        comment: str | None = None,
        model: _Model | None = None,
    ) -> None:
        # Funnel straight to the runtime base: generated __init__ methods are
        # typed sugar, not a cooperative chain (parents' signatures differ).
        _EntityBase.__init__(
            self,
            name,
            label=label,
            comment=comment,
            model=model,
            **_provided(
                actuated_by_property=actuated_by_property,
                cnx=cnx,
                connected=connected,
                connected_from=connected_from,
                connected_through=connected_through,
                connected_to=connected_to,
                contains_=contains_,
                executes=executes,
                has_connection_point=has_connection_point,
                has_optional_connection_point=has_optional_connection_point,
                has_physical_location=has_physical_location,
                has_process=has_process,
                has_property=has_property,
                has_role=has_role,
                has_treatment_objective=has_treatment_objective,
                medium=medium,
            ),
        )

_P_CoagulationStage_has_process = _PropertySpec(
    name='has_process',
    predicate='https://watermetadata.org/ontology/watr#hasProcess',
    kind='class',
    label='has process',
    definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
    ranges=('Process',),
    range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
    sources=('bc09fac0c70bc9398630ec2a2', 'cb172c0e033255224fb32955471031954076a4e16527a4ede2a11cc4196e495ac8e', 'https://watermetadata.org/ontology/watr#hasProcess'),
    min_count=1,
    required=True,
)

_P_CoagulationStage_has_treatment_objective = _PropertySpec(
    name='has_treatment_objective',
    predicate='https://watermetadata.org/ontology/watr#hasTreatmentObjective',
    kind='class',
    label='has treatment objective',
    definition='Associates a piece of equipment or a system with the treatment objective it is intended to achieve. What it does to achieve that is watr:hasProcess.',
    ranges=('TreatmentObjective',),
    range_groups=(('https://watermetadata.org/ontology/watr#TreatmentObjective',),),
    sources=('cb14be08cca11b578ad72e53d419b982daa7fb5dce47d2ac407e95368bcd49d1610', 'https://watermetadata.org/ontology/watr#hasTreatmentObjective'),
)

class CoagulationStage(_BASE.CoagulationBasin):
    """Coagulant addition and particle destabilization ahead of flocculation.

    Ontology: DrinkingWater — https://watermetadata.org/plumb/drinking-water#CoagulationStage
    """

    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/drinking-water#CoagulationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Coagulation stage',
        definition='Coagulant addition and particle destabilization ahead of flocculation.',
        parent_iris=('https://watermetadata.org/ontology/watr#CoagulationBasin',),
        ancestor_iris=('http://data.ashrae.org/standard223#Concept', 'http://data.ashrae.org/standard223#Connectable', 'http://data.ashrae.org/standard223#Equipment', 'http://www.w3.org/2000/01/rdf-schema#Resource', 'https://watermetadata.org/ontology/watr#CoagulationBasin', 'https://watermetadata.org/ontology/watr#Reactor', 'https://watermetadata.org/ontology/watr#Tank', 'https://watermetadata.org/ontology/watr#UnitProcess'),
        properties=(_P_CoagulationStage_has_process, _P_CoagulationStage_has_treatment_objective,),
        cp_slots=(
            _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', medium_options=(), min_count=1, max_count=1, name='inlet', label='inlet'),
            _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', medium_options=(), min_count=1, max_count=1, name='outlet', label='outlet'),
        ),
        class_defaults=(('has_process', 'Process_Coagulation'),),
    )

    has_process: _Rel[type[_BASE.Process]] = _Rel(_P_CoagulationStage_has_process)
    """Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape. (https://watermetadata.org/ontology/watr#hasProcess)"""

    has_treatment_objective: _Rel[type[_BASE.TreatmentObjective]] = _Rel(_P_CoagulationStage_has_treatment_objective)
    """Associates a piece of equipment or a system with the treatment objective it is intended to achieve. What it does to achieve that is watr:hasProcess. (https://watermetadata.org/ontology/watr#hasTreatmentObjective)"""
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, cb172c0e033255224fb32955471031954076a4e16527a4ede2a11cc4196e495ac8e, https://watermetadata.org/ontology/watr#hasProcess', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-Coagulation', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'cb14be08cca11b578ad72e53d419b982daa7fb5dce47d2ac407e95368bcd49d1610, https://watermetadata.org/ontology/watr#hasTreatmentObjective', required=(_TermValue('https://watermetadata.org/ontology/watr#TreatmentObjective-TurbidityRemoval', types=()),), defaults=(), choices=None, minimum=0, maximum=None),
    )
    _shape_max_ports = 2
    inlet = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='inlet')
    outlet = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='outlet')
    _point_declarations = {
        'inlet': inlet,
        'outlet': outlet,
    }

    def __init__(
        self,
        name: str | None = None,
        *,
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
        label: str | None = None,
        comment: str | None = None,
        model: _Model | None = None,
    ) -> None:
        # Funnel straight to the runtime base: generated __init__ methods are
        # typed sugar, not a cooperative chain (parents' signatures differ).
        _EntityBase.__init__(
            self,
            name,
            label=label,
            comment=comment,
            model=model,
            **_provided(
                actuated_by_property=actuated_by_property,
                cnx=cnx,
                connected=connected,
                connected_from=connected_from,
                connected_through=connected_through,
                connected_to=connected_to,
                contains_=contains_,
                executes=executes,
                has_connection_point=has_connection_point,
                has_optional_connection_point=has_optional_connection_point,
                has_physical_location=has_physical_location,
                has_process=has_process,
                has_property=has_property,
                has_role=has_role,
                has_treatment_objective=has_treatment_objective,
                medium=medium,
            ),
        )

_P_FlocculationStage_has_process = _PropertySpec(
    name='has_process',
    predicate='https://watermetadata.org/ontology/watr#hasProcess',
    kind='class',
    label='has process',
    definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
    ranges=('Process',),
    range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
    sources=('bc09fac0c70bc9398630ec2a2', 'cb673a4698bea5cc55d6d1597ab783628d1e847b0697741aaeec137d798e5e948a', 'https://watermetadata.org/ontology/watr#hasProcess'),
    min_count=1,
    required=True,
)

_P_FlocculationStage_has_treatment_objective = _PropertySpec(
    name='has_treatment_objective',
    predicate='https://watermetadata.org/ontology/watr#hasTreatmentObjective',
    kind='class',
    label='has treatment objective',
    definition='Associates a piece of equipment or a system with the treatment objective it is intended to achieve. What it does to achieve that is watr:hasProcess.',
    ranges=('TreatmentObjective',),
    range_groups=(('https://watermetadata.org/ontology/watr#TreatmentObjective',),),
    sources=('cb1326af8ed69dab16e7cf90378ac3e8b121b45469b489e8fe9c5a35e71b23f77f3', 'https://watermetadata.org/ontology/watr#hasTreatmentObjective'),
)

class FlocculationStage(_BASE.FlocculationBasin):
    """Gentle mixing to form flocs that can settle in the clarifier.

    Ontology: DrinkingWater — https://watermetadata.org/plumb/drinking-water#FlocculationStage
    """

    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/drinking-water#FlocculationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Flocculation stage',
        definition='Gentle mixing to form flocs that can settle in the clarifier.',
        parent_iris=('https://watermetadata.org/ontology/watr#FlocculationBasin',),
        ancestor_iris=('http://data.ashrae.org/standard223#Concept', 'http://data.ashrae.org/standard223#Connectable', 'http://data.ashrae.org/standard223#Equipment', 'http://www.w3.org/2000/01/rdf-schema#Resource', 'https://watermetadata.org/ontology/watr#FlocculationBasin', 'https://watermetadata.org/ontology/watr#Reactor', 'https://watermetadata.org/ontology/watr#Tank', 'https://watermetadata.org/ontology/watr#UnitProcess'),
        properties=(_P_FlocculationStage_has_process, _P_FlocculationStage_has_treatment_objective,),
        cp_slots=(
            _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', medium_options=(), min_count=1, max_count=1, name='inlet', label='inlet'),
            _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', medium_options=(), min_count=1, max_count=1, name='outlet', label='outlet'),
        ),
        class_defaults=(('has_process', 'Process_Flocculation'),),
    )

    has_process: _Rel[type[_BASE.Process]] = _Rel(_P_FlocculationStage_has_process)
    """Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape. (https://watermetadata.org/ontology/watr#hasProcess)"""

    has_treatment_objective: _Rel[type[_BASE.TreatmentObjective]] = _Rel(_P_FlocculationStage_has_treatment_objective)
    """Associates a piece of equipment or a system with the treatment objective it is intended to achieve. What it does to achieve that is watr:hasProcess. (https://watermetadata.org/ontology/watr#hasTreatmentObjective)"""
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, cb673a4698bea5cc55d6d1597ab783628d1e847b0697741aaeec137d798e5e948a, https://watermetadata.org/ontology/watr#hasProcess', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-Flocculation', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'cb1326af8ed69dab16e7cf90378ac3e8b121b45469b489e8fe9c5a35e71b23f77f3, https://watermetadata.org/ontology/watr#hasTreatmentObjective', required=(_TermValue('https://watermetadata.org/ontology/watr#TreatmentObjective-TurbidityRemoval', types=()),), defaults=(), choices=None, minimum=0, maximum=None),
    )
    _shape_max_ports = 2
    inlet = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='inlet')
    outlet = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='outlet')
    _point_declarations = {
        'inlet': inlet,
        'outlet': outlet,
    }

    def __init__(
        self,
        name: str | None = None,
        *,
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
        label: str | None = None,
        comment: str | None = None,
        model: _Model | None = None,
    ) -> None:
        # Funnel straight to the runtime base: generated __init__ methods are
        # typed sugar, not a cooperative chain (parents' signatures differ).
        _EntityBase.__init__(
            self,
            name,
            label=label,
            comment=comment,
            model=model,
            **_provided(
                actuated_by_property=actuated_by_property,
                cnx=cnx,
                connected=connected,
                connected_from=connected_from,
                connected_through=connected_through,
                connected_to=connected_to,
                contains_=contains_,
                executes=executes,
                has_connection_point=has_connection_point,
                has_optional_connection_point=has_optional_connection_point,
                has_physical_location=has_physical_location,
                has_process=has_process,
                has_property=has_property,
                has_role=has_role,
                has_treatment_objective=has_treatment_objective,
                medium=medium,
            ),
        )

_P_RapidSandFiltrationStage_has_process = _PropertySpec(
    name='has_process',
    predicate='https://watermetadata.org/ontology/watr#hasProcess',
    kind='class',
    label='has process',
    definition='Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape.',
    ranges=('Process',),
    range_groups=(('https://watermetadata.org/ontology/watr#Process',),),
    sources=('bc09fac0c70bc9398630ec2a2', 'cb1646f6a6b21cab8cbfcf97528ad0560db127964549809ee2057975a54b4bff291', 'https://watermetadata.org/ontology/watr#hasProcess'),
    min_count=1,
    required=True,
)

_P_RapidSandFiltrationStage_has_treatment_objective = _PropertySpec(
    name='has_treatment_objective',
    predicate='https://watermetadata.org/ontology/watr#hasTreatmentObjective',
    kind='class',
    label='has treatment objective',
    definition='Associates a piece of equipment or a system with the treatment objective it is intended to achieve. What it does to achieve that is watr:hasProcess.',
    ranges=('TreatmentObjective',),
    range_groups=(('https://watermetadata.org/ontology/watr#TreatmentObjective',),),
    sources=('cb1b45607b38c7a00dd4e618c308c6ce9f6a7b7c7f4f442f5efd3b0ad7e0b18c3f5', 'https://watermetadata.org/ontology/watr#hasTreatmentObjective'),
)

class RapidSandFiltrationStage(_BASE.RapidSandFilter):
    """Filters clarified water through sand; spent backwash leaves separately during cleaning.

    Ontology: DrinkingWater — https://watermetadata.org/plumb/drinking-water#RapidSandFiltrationStage
    """

    _classinfo = _ClassInfo(
        iri='https://watermetadata.org/plumb/drinking-water#RapidSandFiltrationStage',
        ontology=ONTOLOGY,
        registry=_REGISTRY,
        label='Rapid sand filtration stage',
        definition='Filters clarified water through sand; spent backwash leaves separately during cleaning.',
        parent_iris=('https://watermetadata.org/ontology/watr#RapidSandFilter',),
        ancestor_iris=('http://data.ashrae.org/standard223#Concept', 'http://data.ashrae.org/standard223#Connectable', 'http://data.ashrae.org/standard223#Equipment', 'http://data.ashrae.org/standard223#Filter', 'http://www.w3.org/2000/01/rdf-schema#Resource', 'https://watermetadata.org/ontology/watr#Filter', 'https://watermetadata.org/ontology/watr#MediaFiltrationUnit', 'https://watermetadata.org/ontology/watr#RapidSandFilter', 'https://watermetadata.org/ontology/watr#UnitProcess'),
        properties=(_P_RapidSandFiltrationStage_has_process, _P_RapidSandFiltrationStage_has_treatment_objective,),
        cp_slots=(
            _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', medium_options=(), min_count=1, max_count=1, name='backwash_supply', label='backwash_supply'),
            _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', medium_options=(), min_count=1, max_count=1, name='backwash_waste', label='backwash_waste'),
            _CPSlot(cp_class='OutletConnectionPoint', direction='out', medium='http://data.ashrae.org/standard223#Fluid-Water', medium_options=(), min_count=1, max_count=1, name='filtered_water', label='filtered_water'),
            _CPSlot(cp_class='InletConnectionPoint', direction='in', medium='http://data.ashrae.org/standard223#Fluid-Water', medium_options=(), min_count=1, max_count=1, name='inlet', label='inlet'),
        ),
        class_defaults=(('has_process', 'Process_RapidSandFiltration'),),
    )

    has_process: _Rel[type[_BASE.Process]] = _Rel(_P_RapidSandFiltrationStage_has_process)
    """Associates a water treatment process with the entity that performs it: a piece of Equipment, or an s223:System where the process is performed by the collection and by no individual member (backwashing, or a treatment train such as an MLE). See watr:ProcessBearerShape and watr:ProcessValueShape. (https://watermetadata.org/ontology/watr#hasProcess)"""

    has_treatment_objective: _Rel[type[_BASE.TreatmentObjective]] = _Rel(_P_RapidSandFiltrationStage_has_treatment_objective)
    """Associates a piece of equipment or a system with the treatment objective it is intended to achieve. What it does to achieve that is watr:hasProcess. (https://watermetadata.org/ontology/watr#hasTreatmentObjective)"""
    _shape_constraints = (
        _ShapeValues('has_process', 'bc09fac0c70bc9398630ec2a2, cb1646f6a6b21cab8cbfcf97528ad0560db127964549809ee2057975a54b4bff291, https://watermetadata.org/ontology/watr#hasProcess', required=(_TermValue('https://watermetadata.org/ontology/watr#Process-RapidSandFiltration', types=()),), defaults=(), choices=None, minimum=1, maximum=None),
        _ShapeValues('has_treatment_objective', 'cb1b45607b38c7a00dd4e618c308c6ce9f6a7b7c7f4f442f5efd3b0ad7e0b18c3f5, https://watermetadata.org/ontology/watr#hasTreatmentObjective', required=(_TermValue('https://watermetadata.org/ontology/watr#TreatmentObjective-TurbidityRemoval', types=()),), defaults=(), choices=None, minimum=0, maximum=None),
    )
    _shape_max_ports = 4
    backwash_supply = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='backwash_supply')
    backwash_waste = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='backwash_waste')
    filtered_water = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='out', label='filtered_water')
    inlet = _PointDeclaration[_PointRef](count=1, medium=_REGISTRY.resolve_enum('http://data.ashrae.org/standard223#Fluid-Water'), direction='in', label='inlet')
    _point_declarations = {
        'backwash_supply': backwash_supply,
        'backwash_waste': backwash_waste,
        'filtered_water': filtered_water,
        'inlet': inlet,
    }

    def __init__(
        self,
        name: str | None = None,
        *,
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
        label: str | None = None,
        comment: str | None = None,
        model: _Model | None = None,
    ) -> None:
        # Funnel straight to the runtime base: generated __init__ methods are
        # typed sugar, not a cooperative chain (parents' signatures differ).
        _EntityBase.__init__(
            self,
            name,
            label=label,
            comment=comment,
            model=model,
            **_provided(
                actuated_by_property=actuated_by_property,
                cnx=cnx,
                connected=connected,
                connected_from=connected_from,
                connected_through=connected_through,
                connected_to=connected_to,
                contains_=contains_,
                executes=executes,
                has_connection_point=has_connection_point,
                has_optional_connection_point=has_optional_connection_point,
                has_physical_location=has_physical_location,
                has_process=has_process,
                has_property=has_property,
                has_role=has_role,
                has_treatment_objective=has_treatment_objective,
                medium=medium,
            ),
        )

__all__ = ['ONTOLOGY', 'REGISTRY', 'ChlorinationStage', 'ClarificationStage', 'CoagulationStage', 'FlocculationStage', 'RapidSandFiltrationStage']
