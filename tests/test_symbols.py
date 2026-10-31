"""Compiler dependency exports preserve semantics without loading Python classes."""

import json
import sys

import pytest
from rdflib import Graph

from plumb.gen import compile_modules, extract
from plumb.gen.symbols import FILENAME, FORMAT, Symbols


def test_dependency_symbols_keep_effective_constraints_and_ancestry():
    graph = Graph().parse(
        data="""
        @prefix ex: <urn:symbols#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        ex:A a owl:Class, sh:NodeShape ;
            sh:property [ sh:path ex:member ; sh:class ex:A ; sh:maxCount 3 ] .
        ex:B a owl:Class, sh:NodeShape ; rdfs:subClassOf ex:A ;
            sh:property [ sh:path ex:member ; sh:class ex:B ; sh:minCount 2 ] .
    """,
        format="turtle",
    )
    output = compile_modules(graph, name="Symbols")
    symbols = Symbols.decode(output[FILENAME], module="symbols")
    expected = extract(graph, name="Symbols")
    original = next(cls for cls in expected.classes if cls.name == "B")
    actual = symbols.classes[original.iri]
    prop = actual.effective_props["member"]
    assert prop.ranges == ("B",)
    assert (prop.min_count, prop.max_count) == (2, 3)
    assert actual.ancestor_iris == original.ancestor_iris
    assert len(symbols.digest) == 64


def test_loading_dependency_never_executes_parent_packages(tmp_path, monkeypatch):
    parent = tmp_path / "unimportable_dependency"
    leaf = parent / "base"
    leaf.mkdir(parents=True)
    for path in (parent, leaf):
        (path / "__init__.py").write_text("raise AssertionError('must not import')")
    (leaf / FILENAME).write_text(
        json.dumps(
            {
                "format": FORMAT,
                "ontology": {"iri": "urn:base"},
                "classes": [],
                "enums": [],
                "properties": {},
            }
        )
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    assert Symbols.load("unimportable_dependency.base").ontology["iri"] == "urn:base"
    assert "unimportable_dependency" not in sys.modules
    assert "unimportable_dependency.base" not in sys.modules


def test_dependency_format_and_missing_exports_are_actionable(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="unsupported compiler dependency format"):
        Symbols.decode('{"format": 99}', module="bad")
    package = tmp_path / "missing_symbols"
    package.mkdir()
    (package / "__init__.py").write_text("")
    monkeypatch.syspath_prepend(str(tmp_path))
    with pytest.raises(ValueError, match="regenerate the base package"):
        Symbols.load("missing_symbols")
