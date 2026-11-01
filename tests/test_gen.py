"""The compiler: fixture ontology -> generated module -> working classes."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import rdflib

from plumb import Model, ModelingError
from plumb.gen import compile_modules, compile_source, extract, generate
from plumb.gen import naming
from plumb.gen.overlays import Binding, Overlay

FIXTURE = Path(__file__).parent / "fixtures" / "mini.ttl"

MINI_OVERLAY = Overlay(
    rshift={"Equipment": "feeds"},
    containment=(
        ("Equipment", "Sensor", "has_sensor", "container"),
        # deliberately references a class this ontology doesn't define:
        (Binding("Zone", required=False), "Equipment", "has_location", "child"),
    ),
)

BOOLEAN_CP_TTL = """
@prefix mini: <http://data.ashrae.org/standard223#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .

<urn:boolean> a owl:Ontology .

mini:Coil a owl:Class, sh:NodeShape ;
    sh:xone (
        [ sh:and (
            [ sh:property [
                sh:path mini:hasConnectionPoint ;
                sh:qualifiedValueShape [
                    sh:class mini:InletConnectionPoint ;
                    sh:node [ sh:property [
                        sh:path mini:hasMedium ;
                        sh:class mini:Fluid-Air
                    ] ]
                ] ;
                sh:qualifiedMinCount 1 ;
                sh:qualifiedMaxCount 1
            ] ]
            [ sh:or (
                [ sh:property [
                    sh:path mini:hasConnectionPoint ;
                    sh:qualifiedValueShape [
                        sh:class mini:OutletConnectionPoint ;
                        sh:node [ sh:property [
                            sh:path mini:hasMedium ;
                            sh:class mini:Fluid-Air
                        ] ]
                    ] ;
                    sh:qualifiedMinCount 1
                ] ]
                [ sh:property [
                    sh:path mini:hasConnectionPoint ;
                    sh:qualifiedValueShape [
                        sh:class mini:OutletConnectionPoint ;
                        sh:node [ sh:property [
                            sh:path mini:hasMedium ;
                            sh:class mini:Fluid-Water
                        ] ]
                    ] ;
                    sh:qualifiedMinCount 1
                ] ]
                [ sh:property [
                    sh:path mini:label ;
                    sh:minCount 1
                ] ]
            ) ]
        ) ]
        [ sh:property [
            sh:path mini:hasConnectionPoint ;
            sh:qualifiedValueShape [
                sh:class mini:BidirectionalConnectionPoint ;
                sh:node [ sh:property [
                    sh:path mini:hasMedium ;
                    sh:class mini:Medium-ThermalContact
                ] ]
            ] ;
            sh:qualifiedMinCount 2 ;
            sh:qualifiedMaxCount 3
        ] ]
    ) .

mini:Pump a owl:Class, sh:NodeShape ;
    sh:property [
        sh:path mini:hasConnectionPoint ;
        sh:qualifiedValueShape [
            sh:class mini:OutletConnectionPoint ;
            sh:node [ sh:property [
                sh:path mini:hasMedium ;
                sh:or (
                    [ sh:class mini:Fluid-Water ]
                    [ sh:class mini:Fluid-Air ]
                )
            ] ]
        ] ;
        sh:qualifiedMinCount 1
    ] .

# WaTr places the nested medium constraint directly on the qualified shape.
mini:Tank a owl:Class, sh:NodeShape ;
    sh:property [
        sh:path mini:hasConnectionPoint ;
        sh:qualifiedValueShape [
            sh:class mini:InletConnectionPoint ;
            sh:property [
                sh:path mini:hasMedium ;
                sh:class mini:Fluid-Water
            ]
        ] ;
        sh:qualifiedMinCount 1
    ] .

mini:InletConnectionPoint a owl:Class .
mini:OutletConnectionPoint a owl:Class .
mini:BidirectionalConnectionPoint a owl:Class .
mini:EnumerationKind a owl:Class .
mini:Fluid-Air a owl:Class ; rdfs:subClassOf mini:EnumerationKind .
mini:Fluid-Water a owl:Class ; rdfs:subClassOf mini:EnumerationKind .
mini:Medium-ThermalContact a owl:Class ;
    rdfs:subClassOf mini:EnumerationKind .
"""


@pytest.fixture(scope="module")
def mini(tmp_path_factory):
    """Compile the fixture ontology and import the generated package."""
    graph = rdflib.Graph()
    graph.parse(FIXTURE)
    out = tmp_path_factory.mktemp("gen") / "mini"
    target = generate(
        graph, out, name="Mini", source=str(FIXTURE), overlay=MINI_OVERLAY
    )
    spec = importlib.util.spec_from_file_location("generated_mini", target)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generated_mini"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def m():
    with Model("urn:ex/site#") as model:
        yield model


def test_class_hierarchy(mini):
    assert issubclass(mini.Fan, mini.Equipment)
    assert issubclass(mini.ExhaustFan, mini.Fan)


def test_disambiguation_reserves_intrinsic_suffixed_names():
    result = naming.disambiguate(
        {
            "urn:a#pet": "pet",
            "urn:b#pet": "pet",
            "urn:c#pet_2": "pet_2",
        }
    )
    assert result == {"urn:a#pet": "pet", "urn:b#pet": "pet_3", "urn:c#pet_2": "pet_2"}


def test_ontology_info(mini):
    assert mini.ONTOLOGY.name == "Mini"
    assert mini.ONTOLOGY.iri == "urn:mini"
    assert mini.ONTOLOGY.version == "1.2.3"
    assert mini.ONTOLOGY.source == str(FIXTURE)
    assert Path(mini.__file__).with_name("_shapes.ttl").exists()


def test_package_registry_loads_generated_types(mini, m):
    mini.Fan("fan", has_sensor=[mini.Sensor("sensor")])
    assert "REGISTRY" in mini.__all__
    assert mini.REGISTRY is mini.Fan.meta.registry
    loaded = Model.from_graph(m.graph(), registries=mini.REGISTRY)
    assert isinstance(loaded["fan"], mini.Fan)
    assert isinstance(loaded["sensor"], mini.Sensor)


@pytest.mark.parametrize("name", ["ONTOLOGY", "REGISTRY"])
def test_class_names_preserve_package_metadata_exports(name):
    assert naming.class_name(f"urn:test#{name}") == name + "_"


def test_docstrings_carry_ontology_documentation(mini):
    assert "Moves air using rotating blades." in mini.Fan.__doc__
    assert "urn:mini#Fan" in mini.Fan.__doc__  # provenance in the docstring
    # rdfs:comment is the fallback when skos:definition is absent
    assert "Measures a physical quantity." in mini.Sensor.__doc__


def test_meta_matches_docstrings(mini):
    assert mini.Fan.meta.definition == "Moves air using rotating blades."
    assert mini.Fan.meta.label == "Fan"
    assert mini.Fan.meta.ontology.version == "1.2.3"


def test_property_names_are_snake_cased(mini, m):
    fan = mini.Fan("f1", has_sensor=[mini.Sensor("s1")])
    assert hasattr(fan, "is_fed_by")
    assert hasattr(fan, "rated_power")


def test_s223_point_property_names_are_canonical_and_iri_scoped():
    assert (
        naming.property_name("http://data.ashrae.org/standard223#hasMedium") == "medium"
    )
    assert (
        naming.property_name("http://data.ashrae.org/standard223#isConnectionPointOf")
        == "owner"
    )
    assert (
        naming.property_name("http://data.ashrae.org/standard223#connectsThrough")
        == "connection"
    )
    assert (
        naming.property_name("http://data.ashrae.org/standard223#pairedConnectionPoint")
        == "paired_with"
    )
    assert naming.property_name("https://example.test/Brick#hasMedium") == "has_medium"


def test_emitter_exposes_only_the_canonical_point_descriptor():
    graph = rdflib.Graph()
    s223 = rdflib.Namespace("http://data.ashrae.org/standard223#")
    graph.add((s223.ConnectionPoint, rdflib.RDF.type, rdflib.OWL.Class))
    graph.add((s223.hasMedium, rdflib.RDF.type, rdflib.OWL.ObjectProperty))
    graph.add((s223.hasMedium, rdflib.RDFS.domain, s223.ConnectionPoint))

    source = compile_source(graph, name="S223", overlay=None)

    assert "name='medium'" in source
    assert "predicate='http://data.ashrae.org/standard223#hasMedium'" in source
    assert "medium: _Rel[_EntityBase]" in source
    assert "PropertyAlias" not in source
    assert "has_medium" not in source


def test_shacl_min_count_becomes_required(mini, m):
    # The generated signature itself rejects the omission (this is what the
    # IDE/type checker sees too)...
    with pytest.raises(TypeError, match="has_sensor"):
        mini.Fan("f1")
    # ...and the runtime net still catches an explicitly-empty collection.
    with pytest.raises(ModelingError, match="missing required property: has_sensor"):
        mini.Fan("f1", has_sensor=[])
    import inspect

    param = inspect.signature(mini.Fan.__init__).parameters["has_sensor"]
    assert param.default is inspect.Parameter.empty


def test_shacl_max_count_one_becomes_scalar(mini, m):
    fan = mini.Fan("f1", has_sensor=[mini.Sensor("s1")])
    system = mini.System("sys1")
    fan.part_of_system = system
    assert fan.part_of_system is system


def test_generated_init_allows_omitting_name(mini, m):
    fan = mini.Fan(has_sensor=[mini.Sensor()])
    assert fan.name == "fan_1"
    assert m["sensor_1"] in fan.has_sensor


def test_plain_equipment_is_unconstrained(mini, m):
    eq = mini.Equipment("e1")  # no SHACL narrowing on the parent
    assert list(eq.has_sensor) == []


def test_inverse_maintained_from_owl_inverse_of(mini, m):
    a = mini.Equipment("a")
    b = mini.Equipment("b")
    a.feeds.add(b)
    assert a in b.is_fed_by


def test_overlay_rshift_and_containment(mini, m):
    a = mini.Equipment("a")
    b = mini.Equipment("b")
    a >> b
    assert b in a.feeds
    with mini.Fan("f1", has_sensor=[mini.Sensor("seed")]) as fan:
        s2 = mini.Sensor("s2")
    assert s2 in fan.has_sensor


def test_overlay_entries_for_missing_classes_are_skipped(mini):
    report = json.loads(Path(mini.__file__).with_name("_support.json").read_text())
    record = next(item for item in report["bindings"] if "Zone" in item["target"])
    assert record["status"] == "missing"
    assert not record["required"]


def test_serialization_uses_ontology_predicates(mini, m):
    from rdflib import Literal, URIRef

    mini.Fan("f1", has_sensor=[mini.Sensor("s1")], rated_power=0.75)
    g = m.graph()
    f1 = URIRef("urn:ex/site#f1")
    assert (f1, URIRef("urn:mini#hasSensor"), URIRef("urn:ex/site#s1")) in g
    assert (f1, URIRef("urn:mini#ratedPower"), Literal(0.75)) in g


def test_generation_is_deterministic():
    graph = rdflib.Graph()
    graph.parse(FIXTURE)
    one = compile_source(graph, name="Mini", source="x", overlay=MINI_OVERLAY)
    reparsed = rdflib.Graph()
    reparsed.parse(FIXTURE)
    two = compile_source(reparsed, name="Mini", source="x", overlay=MINI_OVERLAY)
    assert one == two


def test_generation_ignores_input_order_and_blank_node_labels():
    source = rdflib.Graph().parse(data=BOOLEAN_CP_TTL, format="turtle")
    source.parse(FIXTURE)
    triples = sorted(source)

    def assembled(order):
        relabel: dict[rdflib.BNode, rdflib.BNode] = {}

        def fresh(term):
            if isinstance(term, rdflib.BNode):
                return relabel.setdefault(term, rdflib.BNode())
            return term

        graph = rdflib.Graph()
        for s, p, o in order:
            graph.add((fresh(s), p, fresh(o)))
        return compile_modules(graph, name="Mini", overlay=MINI_OVERLAY)

    assert assembled(triples) == assembled(reversed(triples))


def test_punned_enum_is_emitted_only_as_reference_instance():
    graph = rdflib.Graph().parse(
        data=BOOLEAN_CP_TTL
        + """
            @prefix mini: <http://data.ashrae.org/standard223#> .
            @prefix owl: <http://www.w3.org/2002/07/owl#> .
            mini:Fluid-Air a owl:NamedIndividual, mini:EnumerationKind .
        """,
        format="turtle",
    )
    modules = compile_modules(
        graph,
        name="Boolean",
        overlay=Overlay(enum_root="http://data.ashrae.org/standard223#EnumerationKind"),
    )

    assert "class Fluid_Air" not in modules["__init__.py"]
    assert "_E_Fluid_Air = _EnumValue(" in modules["enums.py"]
    assert "    Fluid_Air = _E_Fluid_Air" in modules["enums.py"]


def test_enum_constituents_are_emitted():
    graph = rdflib.Graph().parse(
        data="""
            @prefix ex: <urn:media#> .
            @prefix owl: <http://www.w3.org/2002/07/owl#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix s223: <http://data.ashrae.org/standard223#> .
            <urn:media> a owl:Ontology .
            ex:EnumerationKind a owl:Class .
            ex:Fluid a owl:Class ; rdfs:subClassOf ex:EnumerationKind .
            ex:Constituent a owl:Class ; rdfs:subClassOf ex:EnumerationKind .
            ex:Constituent-H2O a owl:Class ; rdfs:subClassOf ex:Constituent .
            ex:Constituent-NaCl a owl:Class ; rdfs:subClassOf ex:Constituent .
            ex:Fluid-Brine a owl:Class ;
                rdfs:subClassOf ex:Fluid ;
                s223:composedOf [ s223:ofConstituent ex:Constituent-NaCl ],
                    [ s223:ofConstituent ex:Constituent-H2O ] .
        """,
        format="turtle",
    )
    modules = compile_modules(
        graph, name="Media", overlay=Overlay(enum_root="urn:media#EnumerationKind")
    )

    assert (
        "_E_Fluid_Brine.constituents = (_E_Constituent_H2O, _E_Constituent_NaCl,)"
        in modules["enums.py"]
    )
    assert "_E_Fluid.constituents" not in modules["enums.py"]


def test_multiple_inheritance_constructor_unions_parent_properties():
    graph = rdflib.Graph().parse(
        data="""
            @prefix ex: <urn:mi#> .
            @prefix owl: <http://www.w3.org/2002/07/owl#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            <urn:mi> a owl:Ontology .
            ex:A a owl:Class .
            ex:B a owl:Class .
            ex:C a owl:Class ; rdfs:subClassOf ex:A, ex:B .
            ex:a a owl:DatatypeProperty ; rdfs:domain ex:A .
            ex:b a owl:DatatypeProperty ; rdfs:domain ex:B .
        """,
        format="turtle",
    )
    source = compile_source(graph, name="MI", overlay=None)
    c_source = source.split("class C(A, B):", 1)[1]

    assert "def __init__(" in c_source
    signature = c_source.split("def __init__(", 1)[1].split(") -> None:", 1)[0]
    assert "a:" in signature
    assert "b:" in signature


def test_has_value_is_scalar_and_sparql_shape_does_not_loosen_it():
    graph = rdflib.Graph().parse(
        data="""
            @prefix ex: <urn:value#> .
            @prefix owl: <http://www.w3.org/2002/07/owl#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix sh: <http://www.w3.org/ns/shacl#> .
            <urn:value> a owl:Ontology .
            ex:Property a owl:Class, sh:NodeShape ;
                sh:property [
                    sh:path <http://data.ashrae.org/standard223#hasValue> ;
                    sh:maxCount 1
                ] .
            ex:QuantifiableProperty a owl:Class, sh:NodeShape ;
                rdfs:subClassOf ex:Property ;
                sh:property [
                    sh:path <http://data.ashrae.org/standard223#hasValue> ;
                    sh:message "SPARQL-only semantic constraint"
                ] .
        """,
        format="turtle",
    )
    ir = extract(graph, name="Value")
    prop = next(item for item in ir.classes if item.name == "Property")
    quantifiable = next(
        item for item in ir.classes if item.name == "QuantifiableProperty"
    )

    has_value = next(item for item in prop.own_props if item.name == "has_value")
    assert has_value.kind == "value"
    assert has_value.max_count == 1
    assert all(item.name != "has_value" for item in quantifiable.own_props)


def test_boolean_shacl_connection_constraints_are_preserved():
    graph = rdflib.Graph().parse(data=BOOLEAN_CP_TTL, format="turtle")
    ir = extract(
        graph,
        name="Boolean",
        enum_root="http://data.ashrae.org/standard223#EnumerationKind",
    )
    coil = next(cls for cls in ir.classes if cls.name == "Coil")

    assert coil.cp_slots == []  # alternatives must not become unconditional
    assert len(coil.cp_constraints) == 1
    xone = coil.cp_constraints[0]
    assert xone.operator == "xone"
    assert [child.operator for child in xone.children] == ["and", "slot"]

    inlet, outlets = xone.children[0].children
    assert inlet.slot is not None
    assert inlet.slot.direction == "in"
    assert inlet.slot.medium == "http://data.ashrae.org/standard223#Fluid-Air"
    assert inlet.slot.max_count == 1
    assert outlets.operator == "or"
    assert [child.operator for child in outlets.children] == [
        "slot",
        "slot",
        "opaque",
    ]
    assert [child.slot.medium for child in outlets.children if child.slot] == [
        "http://data.ashrae.org/standard223#Fluid-Air",
        "http://data.ashrae.org/standard223#Fluid-Water",
    ]

    bidirectional = xone.children[1].slot
    assert bidirectional is not None
    assert bidirectional.direction == "bi"
    assert bidirectional.min_count == 2
    assert bidirectional.max_count == 3


def test_boolean_connection_constraints_are_emitted():
    graph = rdflib.Graph().parse(data=BOOLEAN_CP_TTL, format="turtle")
    source = compile_source(
        graph,
        name="Boolean",
        overlay=Overlay(enum_root="http://data.ashrae.org/standard223#EnumerationKind"),
    )

    assert "cp_constraints=(" in source
    assert "_CPConstraint(operator='xone'" in source
    assert "_CPConstraint(operator='and'" in source
    assert "_CPConstraint(operator='or'" in source
    assert "_CPConstraint(operator='opaque')" in source
    assert "max_count=3" in source
    compile(source, "<generated boolean ontology>", "exec")


def test_nested_medium_or_becomes_slot_domain():
    graph = rdflib.Graph().parse(data=BOOLEAN_CP_TTL, format="turtle")
    ir = extract(
        graph,
        name="Boolean",
        enum_root="http://data.ashrae.org/standard223#EnumerationKind",
    )
    pump = next(cls for cls in ir.classes if cls.name == "Pump")

    assert len(pump.cp_slots) == 1
    assert pump.cp_slots[0].medium is None
    assert pump.cp_slots[0].medium_options == (
        "http://data.ashrae.org/standard223#Fluid-Air",
        "http://data.ashrae.org/standard223#Fluid-Water",
    )


def test_direct_qualified_shape_medium_is_extracted():
    graph = rdflib.Graph().parse(data=BOOLEAN_CP_TTL, format="turtle")
    ir = extract(
        graph,
        name="Boolean",
        enum_root="http://data.ashrae.org/standard223#EnumerationKind",
    )
    tank = next(cls for cls in ir.classes if cls.name == "Tank")

    assert len(tank.cp_slots) == 1
    assert tank.cp_slots[0].medium == "http://data.ashrae.org/standard223#Fluid-Water"


def test_connection_slots_use_iri_paths_and_subclass_ancestry():
    graph = rdflib.Graph().parse(
        data=BOOLEAN_CP_TTL
        + """
        @prefix custom: <urn:custom#> .
        custom:CustomInlet a owl:Class ; rdfs:subClassOf mini:InletConnectionPoint .
        custom:InletConnectionPoint a owl:Class .
        custom:Pump a owl:Class, sh:NodeShape ;
            sh:property [ sh:path mini:hasConnectionPoint ;
                sh:qualifiedValueShape [ sh:class custom:CustomInlet ] ;
                sh:qualifiedMinCount 2 ] .
        custom:WrongPath a owl:Class, sh:NodeShape ;
            sh:property [ sh:path custom:hasConnectionPoint ;
                sh:qualifiedValueShape [ sh:class mini:InletConnectionPoint ] ;
                sh:qualifiedMinCount 2 ] .
        custom:WrongClass a owl:Class, sh:NodeShape ;
            sh:property [ sh:path mini:hasConnectionPoint ;
                sh:qualifiedValueShape [ sh:class custom:InletConnectionPoint ] ;
                sh:qualifiedMinCount 2 ] .
    """,
        format="turtle",
    )
    ir = extract(
        graph,
        name="Ports",
        primary_namespace="urn:custom#",
        enum_root="http://data.ashrae.org/standard223#EnumerationKind",
    )
    classes = {cls.iri: cls for cls in ir.classes}
    (slot,) = classes["urn:custom#Pump"].cp_slots
    assert (slot.cp_class, slot.direction, slot.min_count) == ("CustomInlet", "in", 2)
    assert classes["urn:custom#WrongPath"].cp_slots == []
    assert classes["urn:custom#WrongClass"].cp_slots == []
    # The real S223 class was renamed by the collision, and still means inlet.
    tank = classes["http://data.ashrae.org/standard223#Tank"]
    assert tank.cp_slots[0].cp_class == "InletConnectionPoint_2"
    assert tank.cp_slots[0].direction == "in"


def test_medium_constraints_intersect_across_nested_shapes():
    graph = rdflib.Graph().parse(
        data=BOOLEAN_CP_TTL
        + """
        mini:Fluid a owl:Class ; rdfs:subClassOf mini:EnumerationKind .
        mini:Fluid-Water rdfs:subClassOf mini:Fluid .
        mini:NestedTank a owl:Class, sh:NodeShape ;
            sh:property [ sh:path mini:hasConnectionPoint ;
                sh:qualifiedValueShape [ sh:class mini:InletConnectionPoint ;
                    sh:and (
                        [ sh:property [ sh:path mini:hasMedium ; sh:class mini:Fluid ] ]
                        [ sh:property [ sh:path mini:hasMedium ; sh:class mini:Fluid-Water ] ]
                    ) ] ; sh:qualifiedMinCount 1 ] .
    """,
        format="turtle",
    )
    ir = extract(
        graph,
        name="Ports",
        enum_root="http://data.ashrae.org/standard223#EnumerationKind",
    )
    tank = next(cls for cls in ir.classes if cls.name == "NestedTank")
    assert tank.cp_slots[0].medium == "http://data.ashrae.org/standard223#Fluid-Water"


def test_unrelated_medium_predicate_does_not_select_a_domain():
    graph = rdflib.Graph().parse(
        data=BOOLEAN_CP_TTL
        + """
        mini:OtherTank a owl:Class, sh:NodeShape ;
            sh:property [ sh:path mini:hasConnectionPoint ;
                sh:qualifiedValueShape [ sh:class mini:InletConnectionPoint ;
                    sh:property [ sh:path <urn:custom#hasMedium> ; sh:class mini:Fluid-Water ]
                ] ; sh:qualifiedMinCount 1 ] .
    """,
        format="turtle",
    )
    ir = extract(
        graph,
        name="Ports",
        enum_root="http://data.ashrae.org/standard223#EnumerationKind",
    )
    tank = next(cls for cls in ir.classes if cls.name == "OtherTank")
    assert tank.cp_slots == []  # the unrelated qualifier stays validation-only
    modules = compile_modules(
        graph,
        name="Ports",
        overlay=Overlay(enum_root="http://data.ashrae.org/standard223#EnumerationKind"),
    )
    report = json.loads(modules["_support.json"])["connections"]
    record = next(
        item
        for item in report
        if item["target"] == "http://data.ashrae.org/standard223#OtherTank"
    )
    assert record["support"] == "validation-only"
    assert "urn:custom#hasMedium" in record["reason"]
    assert record["source"]


def test_qualified_max_count_alone_sets_no_minimum():
    graph = rdflib.Graph().parse(
        data=BOOLEAN_CP_TTL
        + """
mini:HeatExchanger a owl:Class, sh:NodeShape ;
    sh:property [
        sh:path mini:hasConnectionPoint ;
        sh:qualifiedValueShape [ sh:class mini:BidirectionalConnectionPoint ] ;
        sh:qualifiedMaxCount 0
    ] .
""",
        format="turtle",
    )
    ir = extract(
        graph,
        name="Boolean",
        enum_root="http://data.ashrae.org/standard223#EnumerationKind",
    )
    exchanger = next(cls for cls in ir.classes if cls.name == "HeatExchanger")

    # SHACL reads a missing qualifiedMinCount as no minimum, so this forbids
    # bidirectional points instead of requiring one and allowing none.
    [slot] = exchanger.cp_slots
    assert (slot.min_count, slot.max_count) == (0, 0)


def test_shacl_target_shapes_supply_domain_and_range():
    graph = rdflib.Graph().parse(
        data="""
            @prefix ex: <urn:targets#> .
            @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix sh: <http://www.w3.org/ns/shacl#> .
            ex:Equipment a rdfs:Class .
            ex:System a rdfs:Class .
            ex:Process a rdfs:Class .
            ex:Other a rdfs:Class .
            ex:hasProcess a rdf:Property .
            ex:BearerShape a sh:NodeShape ;
                sh:targetSubjectsOf ex:hasProcess ;
                sh:or ( [ sh:class ex:Equipment ] [ sh:class ex:System ] ) .
            ex:ValueShape a sh:NodeShape ;
                sh:targetObjectsOf ex:hasProcess ;
                sh:class ex:Process .
        """,
        format="turtle",
    )
    classes = {cls.name: cls for cls in extract(graph, name="Targets").classes}

    for bearer in ("Equipment", "System"):
        (prop,) = classes[bearer].own_props
        assert prop.name == "has_process"
        assert prop.ranges == ("Process",)
    assert classes["Other"].own_props == []


def test_extension_namespace_wins_name_collisions_and_identity():
    graph = rdflib.Graph().parse(
        data="""
            @prefix base: <urn:base#> .
            @prefix ext: <urn:extension#> .
            @prefix owl: <http://www.w3.org/2002/07/owl#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            <urn:base> a owl:Ontology .
            <urn:extension> a owl:Ontology .
            base:Pump a owl:Class .
            ext:Pump a owl:Class ; rdfs:subClassOf base:Pump .
        """,
        format="turtle",
    )
    ir = extract(
        graph,
        name="Extension",
        ontology_iri="urn:extension",
        primary_namespace="urn:extension#",
    )

    names = {cls.iri: cls.name for cls in ir.classes}
    assert ir.ontology_iri == "urn:extension"
    assert names["urn:extension#Pump"] == "Pump"
    assert names["urn:base#Pump"] == "Pump_2"


def test_generated_source_type_checks(mini, tmp_path):
    """The emitted module must satisfy the type checker, not just run."""
    import subprocess

    result = subprocess.run(
        [str(Path(sys.executable).with_name("ty")), "check", mini.__file__],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, result.stdout + result.stderr


CLASS_DEFAULTS_TTL = """
@prefix ex: <urn:defaults#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .

<urn:defaults> a owl:Ontology .

ex:Process a owl:Class .
ex:Settling a owl:Class ; rdfs:subClassOf ex:Process .
ex:Sedimentation a owl:Class ; rdfs:subClassOf ex:Settling .
ex:Coagulation a owl:Class ; rdfs:subClassOf ex:Process .

ex:hasProcess a owl:ObjectProperty ; rdfs:domain ex:Equipment .

ex:Equipment a owl:Class .
ex:Tank a owl:Class ; rdfs:subClassOf ex:Equipment .
ex:Unit a owl:Class, sh:NodeShape ;
    rdfs:subClassOf ex:Equipment ;
    sh:property [ sh:path ex:hasProcess ; sh:class ex:Process ; sh:minCount 1 ] .
ex:Settler a owl:Class, sh:NodeShape ;
    rdfs:subClassOf ex:Tank, ex:Unit ;
    sh:property [
        sh:path ex:hasProcess ;
        sh:qualifiedValueShape [ sh:class ex:Settling ] ;
        sh:qualifiedMinCount 1
    ] .
"""


@pytest.fixture(scope="module")
def defaults_pkg(tmp_path_factory):
    graph = rdflib.Graph().parse(data=CLASS_DEFAULTS_TTL, format="turtle")
    out = tmp_path_factory.mktemp("gen") / "defaults"
    target = generate(
        graph,
        out,
        name="Defaults",
        overlay=Overlay(class_properties=("urn:defaults#hasProcess",)),
    )
    spec = importlib.util.spec_from_file_location("generated_defaults", target)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generated_defaults"] = module
    spec.loader.exec_module(module)
    return module


def test_qualified_class_requirement_becomes_constructor_default(defaults_pkg, m):
    # Settler(Tank, Unit): Python resolves Unit.__init__, where has_process is
    # required, so the generator must emit Settler's own optional signature.
    settler = defaults_pkg.Settler("settler")
    assert list(settler.has_process) == [defaults_pkg.Settling]


def test_class_default_yields_to_supplied_subclass(defaults_pkg, m):
    settler = defaults_pkg.Settler("s", has_process=[defaults_pkg.Sedimentation])
    assert list(settler.has_process) == [defaults_pkg.Sedimentation]


def test_class_default_is_added_beside_unrelated_values(defaults_pkg, m):
    settler = defaults_pkg.Settler("s", has_process=[defaults_pkg.Coagulation])
    assert set(settler.has_process) == {defaults_pkg.Coagulation, defaults_pkg.Settling}


def test_property_without_class_default_stays_required(defaults_pkg, m):
    with pytest.raises(TypeError, match="has_process"):
        defaults_pkg.Unit("u")


def test_untyped_declaration_of_enum_predicate_becomes_enum():
    # Like 223's hasMedium: a SPARQL-only shape on the base class declares
    # the predicate untyped; every typed declaration is an enumeration.
    graph = rdflib.Graph().parse(
        data="""
            @prefix ex: <urn:media#> .
            @prefix owl: <http://www.w3.org/2002/07/owl#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix sh: <http://www.w3.org/ns/shacl#> .
            <urn:media> a owl:Ontology .
            ex:EnumerationKind a owl:Class .
            ex:Medium a owl:Class ; rdfs:subClassOf ex:EnumerationKind .
            ex:Water a owl:Class ; rdfs:subClassOf ex:Medium .
            ex:Concept a owl:Class, sh:NodeShape ;
                sh:property [
                    sh:path ex:hasMedium ;
                    sh:sparql [ sh:select "SELECT $this WHERE { }" ]
                ] .
            ex:Port a owl:Class, sh:NodeShape ;
                rdfs:subClassOf ex:Concept ;
                sh:property [ sh:path ex:hasMedium ; sh:class ex:Medium ] .
        """,
        format="turtle",
    )
    ir = extract(graph, name="Media", enum_root="urn:media#EnumerationKind")
    props = {
        cls.name: next(p for p in cls.own_props if p.name == "has_medium")
        for cls in ir.classes
        if cls.name in {"Concept", "Port"}
    }
    assert props["Concept"].kind == "enum"
    assert props["Concept"].enum_ranges == ()
    assert props["Port"].enum_ranges == ("urn:media#Medium",)


def test_overlay_deferred_properties_widen_types_and_mark_specs():
    graph = rdflib.Graph().parse(
        data="""
            @prefix mini: <urn:deferred#> .
            @prefix owl: <http://www.w3.org/2002/07/owl#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            mini:Sensor a owl:Class .
            mini:at a owl:ObjectProperty ; rdfs:domain mini:Sensor .
            mini:near a owl:ObjectProperty ; rdfs:domain mini:Sensor .
        """,
        format="turtle",
    )
    deferred = compile_source(
        graph,
        name="Deferred",
        overlay=Overlay(deferred_properties=("urn:deferred#at",)),
    )
    plain = compile_source(graph, name="Deferred", overlay=Overlay())

    assert "import DeferredEndpoint as _DeferredEndpoint" in deferred
    assert "at: _RelOne[_EntityBase | _DeferredEndpoint]" in deferred or (
        "at: _Rel[_EntityBase | _DeferredEndpoint]" in deferred
    )
    assert deferred.count("deferred=True") == 1
    assert "_DeferredEndpoint" not in plain
    compile(deferred, "<generated deferred ontology>", "exec")


def test_overlay_sensor_classes_register_only_known_classes():
    graph = rdflib.Graph().parse(
        data="""
            @prefix mini: <urn:sensors#> .
            @prefix owl: <http://www.w3.org/2002/07/owl#> .
            mini:TurbidityMeter a owl:Class .
        """,
        format="turtle",
    )
    kind = "http://qudt.org/vocab/quantitykind/"
    modules = compile_modules(
        graph,
        name="Sensors",
        overlay=Overlay(
            sensor_classes={
                f"{kind}Turbidity": "TurbidityMeter",
                f"{kind}Temperature": Binding("TemperatureSensor", required=False),
            }
        ),
    )
    source = modules["__init__.py"]

    assert (
        f"_REGISTRY.sensor_classes = {{'{kind}Turbidity': 'TurbidityMeter'}}" in source
    )
    record = next(
        item
        for item in json.loads(modules["_support.json"])["bindings"]
        if item["target"] == ["TemperatureSensor"]
    )
    assert record["status"] == "missing" and not record["required"]
