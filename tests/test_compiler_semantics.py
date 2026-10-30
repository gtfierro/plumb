"""Small positive and negative models exercise the compiler/runtime contract."""

import importlib.util
import sys

import pytest
from rdflib import Graph, Namespace, RDF, URIRef

from plumb import Model, ModelingError
from plumb.core.errors import RangeError
from plumb.gen import generate

PREFIXES = """
@prefix ex: <urn:semantics#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
<urn:semantics> a owl:Ontology .
"""


@pytest.fixture
def ontology(tmp_path):
    modules = []

    def compile(body):
        name = f"generated_semantics_{len(modules)}"
        target = generate(
            Graph().parse(data=PREFIXES + body, format="turtle"),
            tmp_path / name,
            name="Semantics",
            overlay=None,
        )
        spec = importlib.util.spec_from_file_location(name, target)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        modules.append(name)
        spec.loader.exec_module(module)
        return module

    yield compile
    for name in modules:
        sys.modules.pop(name, None)


def test_rdf_ancestry_survives_python_mro_repair(ontology):
    api = ontology("""
        ex:A a owl:Class ; rdfs:subClassOf ex:C .
        ex:B a owl:Class .
        ex:C a owl:Class .
        ex:X a owl:Class ; rdfs:subClassOf ex:B, ex:C .
        ex:Y a owl:Class ; rdfs:subClassOf ex:A, ex:B .
        ex:Z a owl:Class ; rdfs:subClassOf ex:X, ex:Y .
        ex:Owner a owl:Class .
        ex:member a owl:ObjectProperty ; rdfs:domain ex:Owner ; rdfs:range ex:Y .
        ex:mark a owl:ObjectProperty ; rdfs:domain ex:Y ; rdfs:range ex:Y .
    """)
    assert api.Z.meta.parents == (api.X, api.Y)
    assert not issubclass(api.Z, api.Y)  # C3 repair removes this Python base.
    assert api.Z.meta.is_a(api.Y)
    assert api.Z in api.Y.meta.descendants
    with Model("urn:instance:"):
        owner = api.Owner()
        member = api.Z()
        owner.member.add(member)
        assert member in owner.member
        member.mark.add(member)
        assert member in member.mark


ANIMALS = """
ex:Animal a owl:Class .
ex:Dog a owl:Class ; rdfs:subClassOf ex:Animal .
ex:Cat a owl:Class ; rdfs:subClassOf ex:Animal .
ex:Tagged a owl:Class .
ex:TaggedDog a owl:Class ; rdfs:subClassOf ex:Dog, ex:Tagged .
ex:Owner a owl:Class, sh:NodeShape ;
    sh:property [ sh:path ex:pet ; sh:class ex:Animal ] .
"""


def test_inherited_range_is_narrowed_instead_of_unioned(ontology):
    api = ontology(
        ANIMALS
        + """
        ex:DogOwner a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:pet ; sh:class ex:Dog ] .
    """
    )
    spec = next(p for p in api.DogOwner.meta.properties if p.name == "pet")
    assert spec.ranges == ("Dog",)
    with Model("urn:instance:"):
        owner = api.DogOwner()
        dog, animal = api.Dog(), api.Animal()
        owner.pet.add(dog)
        with pytest.raises(RangeError, match="Dog"):
            owner.pet.add(animal)
        assert list(owner.pet) == [dog]


def test_alternatives_and_intersections_keep_distinct_meanings(ontology):
    api = ontology(
        ANIMALS
        + """
        ex:TaggedPetOwner a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:pet ;
                sh:or ([ sh:class ex:Dog ] [ sh:class ex:Cat ]) ] ;
            sh:property [ sh:path ex:pet ; sh:class ex:Tagged ] .
    """
    )
    with Model("urn:instance:"):
        owner = api.TaggedPetOwner()
        owner.pet.add(api.TaggedDog())
        with pytest.raises(RangeError):
            owner.pet.add(api.Dog())
        with pytest.raises(RangeError):
            owner.pet.add(api.Tagged())


def test_plain_alternatives_accept_either_branch(ontology):
    api = ontology(
        ANIMALS
        + """
        ex:PetOwner a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:pet ;
                sh:or ([ sh:class ex:Dog ] [ sh:class ex:Cat ]) ] .
    """
    )
    with Model("urn:instance:"):
        owner = api.PetOwner()
        owner.pet.add(api.Dog(), api.Cat())
        with pytest.raises(RangeError):
            owner.pet.add(api.Animal())


def test_multiple_parent_constraints_are_composed(ontology):
    api = ontology(
        ANIMALS
        + """
        ex:DogOwner a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:pet ; sh:class ex:Dog ] .
        ex:TaggedOwner a owl:Class, sh:NodeShape ;
            sh:property [ sh:path ex:pet ; sh:class ex:Tagged ] .
        ex:Combined a owl:Class ; rdfs:subClassOf ex:DogOwner, ex:TaggedOwner .
    """
    )
    with Model("urn:instance:"):
        owner = api.Combined()
        owner.pet.add(api.TaggedDog())
        with pytest.raises(RangeError):
            owner.pet.add(api.Dog())
        with pytest.raises(RangeError):
            owner.pet.add(api.Tagged())


def test_counts_intersect_and_batch_mutations_are_atomic(ontology):
    api = ontology(
        ANIMALS
        + """
        ex:PairOwner a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:pet ; sh:minCount 2 ; sh:maxCount 3 ] .
        ex:Child a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:PairOwner ;
            sh:property [ sh:path ex:pet ; sh:minCount 1 ; sh:maxCount 5 ] .
    """
    )
    spec = next(p for p in api.Child.meta.properties if p.name == "pet")
    assert (spec.min_count, spec.max_count) == (2, 3)
    with Model("urn:instance:"):
        one, two, three, four = (api.Dog() for _ in range(4))
        with pytest.raises(ModelingError, match="missing required"):
            api.Child(pet=[one])
        owner = api.Child(pet=[one, two])
        with pytest.raises(RangeError, match="at most 3"):
            owner.pet.add(three, four)
        assert list(owner.pet) == [one, two]


def test_contradictory_inherited_counts_identify_the_predicate(ontology):
    with pytest.raises(ValueError, match="urn:semantics#pet.*contradictory"):
        ontology(
            ANIMALS
            + """
            ex:Small a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
                sh:property [ sh:path ex:pet ; sh:maxCount 1 ] .
            ex:Large a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Small ;
                sh:property [ sh:path ex:pet ; sh:minCount 2 ] .
        """
        )


def test_nested_conjunctive_shapes_match_direct_constraints(ontology):
    api = ontology(
        ANIMALS
        + """
        ex:DogOwner a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:node [ sh:and (
                [ sh:property [ sh:path ex:pet ; sh:class ex:Dog ] ]
                [ sh:property [ sh:path ex:pet ; sh:maxCount 2 ] ]
            ) ] .
    """
    )
    spec = next(p for p in api.DogOwner.meta.properties if p.name == "pet")
    assert (spec.ranges, spec.max_count) == (("Dog",), 2)
    with Model("urn:instance:"):
        owner = api.DogOwner()
        with pytest.raises(RangeError):
            owner.pet.add(api.Animal())


def test_constructor_cycle_deferral_keeps_semantic_minimum(ontology):
    api = ontology("""
        ex:Parent a owl:Class, sh:NodeShape ;
            sh:property [ sh:path ex:child ; sh:class ex:Child ; sh:minCount 1 ] .
        ex:Child a owl:Class, sh:NodeShape ;
            sh:property [ sh:path ex:parent ; sh:class ex:Parent ; sh:minCount 1 ] .
    """)
    spec = api.Parent.meta.properties[0]
    assert spec.min_count == 1
    assert not spec.required
    with Model("urn:instance:"):
        parent = api.Parent()
        child = api.Child(parent=[parent])
        parent.child.add(child)


def test_property_names_do_not_merge_unrelated_predicates(ontology):
    api = ontology("""
        ex:A a owl:Class .
        ex:B a owl:Class ; rdfs:subClassOf ex:A .
        ex:value a owl:ObjectProperty ; rdfs:domain ex:A ; rdfs:range ex:A .
        <urn:elsewhere#value> a owl:ObjectProperty ;
            rdfs:domain ex:B ; rdfs:range ex:B .
    """)
    specs = api.B.meta.properties
    assert len({spec.name for spec in specs}) == 2
    assert {spec.predicate for spec in specs} == {
        "urn:semantics#value",
        "urn:elsewhere#value",
    }
    with Model("urn:instance:"):
        owner, child = api.B(), api.B()
        for spec in specs:
            getattr(owner, spec.name).add(child)


def test_supported_range_checks_agree_with_shacl(ontology):
    import shifty

    body = (
        ANIMALS
        + """
        ex:DogOwner a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:pet ; sh:class ex:Dog ] .
    """
    )
    api = ontology(body)
    shapes = Graph().parse(data=PREFIXES + body, format="turtle")
    ex = Namespace("urn:semantics#")
    owner, pet = URIRef("urn:owner"), URIRef("urn:pet")
    for value_class, valid in ((api.Animal, False), (api.Dog, True), (api.Cat, False)):
        graph = Graph()
        graph.add((owner, RDF.type, ex.DogOwner))
        graph.add((pet, RDF.type, URIRef(value_class.meta.iri)))
        graph.add((owner, ex.pet, pet))
        conforms, _, _ = shifty.validate(graph, shapes, infer=True)
        assert bool(conforms) == valid
        with Model("urn:instance:"):
            obj = api.DogOwner()
            value = value_class()
            if valid:
                obj.pet.add(value)
            else:
                with pytest.raises(RangeError):
                    obj.pet.add(value)


def test_invalid_replacement_keeps_the_existing_collection(ontology):
    api = ontology(
        ANIMALS
        + """
        ex:DogOwner a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:pet ; sh:class ex:Dog ; sh:maxCount 2 ] .
    """
    )
    with Model("urn:instance:"):
        original = api.Dog()
        owner = api.DogOwner(pet=[original])
        with pytest.raises(RangeError):
            owner.pet = [api.Dog(), api.Animal()]
        assert list(owner.pet) == [original]


def test_cycles_fail_with_an_ontology_identity(ontology):
    with pytest.raises(ValueError, match="urn:semantics#.*cyclic ontology inheritance"):
        ontology("""
            ex:A a owl:Class ; rdfs:subClassOf ex:B .
            ex:B a owl:Class ; rdfs:subClassOf ex:A .
        """)
