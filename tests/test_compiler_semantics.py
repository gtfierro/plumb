"""Small positive and negative models exercise the compiler/runtime contract."""

import importlib.util
import sys

import pytest
from rdflib import Graph

from plumb import Model
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
