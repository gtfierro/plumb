"""The ontology and configuration fronts share one effective constraint contract."""

import importlib
import inspect
import json
import sys

import pytest
from rdflib import Graph

from plumb import Model, ModelingError
from plumb.core.errors import RangeError
from plumb.gen import compile_modules, generate
from plumb.gen.symbols import FILENAME, Symbols

PREFIXES = """
@prefix ex: <urn:front#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix codegen: <https://watermetadata.org/plumb/codegen#> .
"""
BASE = """
<urn:front> a owl:Ontology .
ex:Animal a owl:Class .
ex:Dog a owl:Class ; rdfs:subClassOf ex:Animal .
ex:Cat a owl:Class ; rdfs:subClassOf ex:Animal .
ex:Owner a owl:Class, sh:NodeShape ;
    sh:property [ sh:path ex:pet ; sh:class ex:Animal ; sh:maxCount 3 ] ;
    sh:property [ sh:path ex:mode ; sh:datatype xsd:string ; sh:maxCount 1 ;
                  sh:in ("a" "b") ; sh:defaultValue "a" ] .
"""


@pytest.fixture
def compiler(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(tmp_path))
    base_graph = Graph().parse(data=PREFIXES + BASE, format="turtle")
    generate(base_graph, tmp_path / "front_base", name="Base", overlay=None)
    modules = []

    def build(body, *, configuration=True, dependency="front_base"):
        name = f"front_result_{len(modules)}"
        modules.append(name)
        header = (
            f'<urn:extension> a owl:Ontology ; codegen:baseModule "{dependency}" .'
            if configuration
            else BASE
        )
        graph = Graph().parse(data=PREFIXES + header + body, format="turtle")
        generate(graph, tmp_path / name, name="Front", overlay=None)
        return importlib.import_module(name)

    yield build, tmp_path
    for name in list(sys.modules):
        if name == "front_base" or name.startswith("front_result_"):
            sys.modules.pop(name, None)


@pytest.mark.parametrize("form", ["direct", "node", "and"])
@pytest.mark.parametrize("configuration", [False, True])
def test_equivalent_shapes_have_identical_runtime_constraints(
    compiler, form, configuration
):
    build, _ = compiler
    props = """
        sh:property [ sh:path ex:pet ; sh:class ex:Dog ; sh:maxCount 2 ] ;
        sh:property [ sh:path ex:mode ; sh:in ("b") ; sh:defaultValue "b" ]
    """
    shape = (
        props
        if form == "direct"
        else f"sh:node [ {props} ]"
        if form == "node"
        else f"sh:and ([ {props} ])"
    )
    api = build(
        f"ex:Special a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ; {shape} .",
        configuration=configuration,
    )
    with Model("urn:instance:"):
        owner = api.Special()
        assert owner.mode == "b"
        base = importlib.import_module("front_base") if configuration else api
        dog = base.Dog()
        owner.pet.add(dog)
        setattr(owner, "pet", (value for value in [dog]))
        with pytest.raises(RangeError):
            owner.pet.add(base.Animal())
        with pytest.raises(ModelingError, match="sh:in"):
            owner.mode = "a"
        assert owner.mode == "b"
        with pytest.raises(RangeError, match="at most 2"):
            owner.pet.add(base.Dog(), base.Dog())
        assert list(owner.pet) == [dog]


@pytest.mark.parametrize("configuration", [False, True])
def test_inherited_defaults_and_empty_choices(compiler, configuration):
    build, _ = compiler
    api = build(
        """
        ex:Special a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:pet ; sh:in () ] .
    """,
        configuration=configuration,
    )
    with Model("urn:instance:"):
        owner = api.Special()
        assert owner.mode == "a"
        base = importlib.import_module("front_base") if configuration else api
        with pytest.raises(ModelingError, match="sh:in"):
            owner.pet.add(base.Dog())


@pytest.mark.parametrize("configuration", [False, True])
def test_disallowed_inherited_default_fails_compilation(compiler, configuration):
    build, _ = compiler
    with pytest.raises(ValueError, match="outside sh:in"):
        build(
            """
            ex:Special a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
                sh:property [ sh:path ex:mode ; sh:in ("b") ] .
        """,
            configuration=configuration,
        )


@pytest.mark.parametrize("configuration", [False, True])
def test_required_values_allow_only_consistent_refinements(compiler, configuration):
    build, _ = compiler
    api = build(
        """
        ex:Special a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:mode ; sh:hasValue "a" ] .
    """,
        configuration=configuration,
    )
    with Model("urn:instance:"):
        owner = api.Special()
        assert owner.mode == "a"
        with pytest.raises(ModelingError, match="sh:hasValue"):
            owner.mode = "b"


def test_configuration_compilation_does_not_execute_its_base(compiler):
    _, root = compiler
    (root / "front_base/__init__.py").write_text(
        "raise AssertionError('must not import')"
    )
    graph = Graph().parse(
        data=PREFIXES
        + """
        <urn:extension> a owl:Ontology ; codegen:baseModule "front_base" .
        ex:Special a owl:Class ; rdfs:subClassOf ex:Owner .
    """,
        format="turtle",
    )
    assert (
        "class Special(_BASE.Owner)"
        in compile_modules(graph, name="Extension")["__init__.py"]
    )
    assert "front_base" not in sys.modules


@pytest.mark.parametrize("configuration", [False, True])
def test_minimum_is_checked_at_construction_and_validation(compiler, configuration):
    build, _ = compiler
    api = build(
        """
        ex:Special a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:pet ; sh:minCount 2 ] .
    """,
        configuration=configuration,
    )
    base = importlib.import_module("front_base") if configuration else api
    with Model("urn:instance:") as model:
        one, two = base.Dog(), base.Dog()
        with pytest.raises(ModelingError, match="missing required"):
            api.Special(pet=[one])
        owner = api.Special(pet=[one, two])
        assert model.validate()
        owner.pet.remove(two)
        assert not model.validate()


def test_configuration_ranges_can_reference_a_local_subclass(compiler):
    build, _ = compiler
    api = build("""
        ex:SpecialDog a owl:Class ; rdfs:subClassOf ex:Dog .
        ex:Special a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:pet ; sh:class ex:SpecialDog ] .
    """)
    with Model("urn:instance:"):
        owner = api.Special(pet=[api.SpecialDog()])
        with pytest.raises(RangeError):
            owner.pet.add(importlib.import_module("front_base").Dog())


def test_linked_extensions_use_exports_and_reject_stale_dependencies(compiler):
    build, root = compiler
    first = build("ex:Special a owl:Class ; rdfs:subClassOf ex:Owner .")
    second = build(
        """
        ex:Derived a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Special ;
            sh:property [ sh:path ex:pet ; sh:class ex:Dog ] .
    """,
        dependency=first.__name__,
    )
    with Model("urn:instance:"):
        obj = second.Derived()
        assert obj.mode == "a"
        obj.pet.add(importlib.import_module("front_base").Dog())
    export = json.loads((root / second.__name__ / FILENAME).read_text())
    assert {item["iri"] for item in export["classes"]} == {"urn:front#Derived"}
    assert (
        Symbols.load(second.__name__).classes["urn:front#Owner"].python_module
        == "front_base"
    )
    path = root / "front_base" / FILENAME
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="regenerate the dependent package"):
        Symbols.load(second.__name__)


@pytest.mark.parametrize("configuration", [False, True])
def test_both_frontends_report_runtime_and_validation_boundaries(
    compiler, configuration
):
    build, root = compiler
    api = build(
        """
        ex:Special a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property ex:SpecialMode .
        ex:SpecialMode sh:path ex:mode ; sh:defaultValue "b" ; sh:in ("b") ;
            sh:sparql [ sh:select "SELECT $this WHERE { FILTER(false) }" ] .
    """,
        configuration=configuration,
    )
    report = json.loads((root / api.__name__ / "_support.json").read_text())
    records = {
        item["parameter"].rsplit("#", 1)[-1]: item
        for item in report["constraints"]
        if item["source"] == "urn:front#SpecialMode"
    }
    assert records["in"]["enforcement"] == ["runtime", "validation"]
    assert records["defaultValue"]["enforcement"] == ["constructor"]
    assert records["sparql"]["enforcement"] == ["validation"]


@pytest.mark.parametrize("configuration", [False, True])
def test_named_reference_defaults_preserve_declared_subtype(compiler, configuration):
    build, root = compiler
    api = build(
        """
        ex:Rover a ex:Dog .
        ex:Special a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:favourite ; sh:class ex:Animal ;
                          sh:maxCount 1 ; sh:hasValue ex:Rover ] .
    """,
        configuration=configuration,
    )
    with Model("urn:instance:"):
        owner = api.Special()
        assert owner.favourite.iri == "urn:front#Rover"
        assert "urn:front#Dog" in owner.favourite.types
    source = (root / api.__name__ / "__init__.py").read_text()
    assert "_TermValue]" in source


@pytest.mark.parametrize("configuration", [False, True])
def test_emitted_class_and_constructor_match_exported_ir(compiler, configuration):
    build, _ = compiler
    api = build(
        """
        ex:Special a owl:Class ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:pet ; sh:class ex:Dog ;
                          sh:minCount 2 ; sh:maxCount 2 ],
                        [ sh:path ex:mode ; sh:defaultValue "b" ; sh:in ("b") ] .
        """,
        configuration=configuration,
    )
    symbol = Symbols.load(api.__name__).classes["urn:front#Special"]
    assert (
        tuple(parent.meta.iri for parent in api.Special.meta.parents)
        == symbol.parent_iris
    )
    actual = {prop.name: prop for prop in api.Special.meta.properties}
    for name, expected in symbol.effective_props.items():
        assert actual[name].predicate == expected.predicate
        assert actual[name].range_groups == expected.range_groups
        assert actual[name].min_count == expected.min_count
        assert actual[name].max_count == expected.max_count
    signature = inspect.signature(api.Special)
    assert signature.parameters["pet"].default is inspect.Parameter.empty
    assert signature.parameters["mode"].default is not inspect.Parameter.empty


def test_configuration_term_constructor_accepts_compiled_reference(compiler):
    from plumb import TermValue

    build, _ = compiler
    api = build("""
        ex:Special a owl:Class ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:tag ; sh:hasValue ex:Tag ] .
    """)
    annotation = inspect.signature(api.Special).parameters["tag"].annotation
    assert "_TermValue" in annotation
    with Model("urn:term:"):
        assert api.Special(tag=TermValue("urn:front#Tag")).tag.iri == "urn:front#Tag"


@pytest.mark.parametrize("configuration", [False, True])
def test_explicit_empty_collection_replaces_shape_default(compiler, configuration):
    build, _ = compiler
    api = build(
        """
        ex:Rover a ex:Dog .
        ex:Special a owl:Class ; rdfs:subClassOf ex:Owner ;
            sh:property [ sh:path ex:pet ; sh:defaultValue ex:Rover ] .
        """,
        configuration=configuration,
    )
    with Model("urn:defaults:"):
        assert len(api.Special().pet) == 1
        assert list(api.Special(pet=()).pet) == []
        assert list(api.Special(pet=[]).pet) == []
    assert inspect.signature(api.Special).parameters["pet"].default is None
