# Extension compiler

`plumb gen` compiles an ontology and its SHACL shapes into a Python
package. For a walk-through, see
[Generate a domain API](../how-to/generate-domain-api.md).

## Command line

```bash
# a local ontology file
plumb gen --file pumps.ttl --name Pumps --out pumps

# by IRI: ontoenv resolves and merges the owl:imports closure
plumb gen --iri https://example.org/ontology/pumps --name Pumps --out pumps

# merge extra graphs, such as shapes published separately
plumb gen --file core.ttl --extra shapes.ttl --name Pumps --out pumps
```

`--source` records where the ontology came from in the package metadata. The
output is a package directory with:

- `__init__.py`: the generated classes, property schemas, and `REGISTRY`;
- `enums.py`, when the ontology has a punned enumeration hierarchy;
- `_shapes.ttl`: the exact graph used for compilation, which `validate()`
  checks against.

The package also carries `_symbols.json` for compiler linking and `_support.json`
for constraint enforcement and source diagnostics. To review an upgrade, save the
old generated package before regenerating, then compare the two directories:

```bash
plumb diff saved-pumps pumps
plumb diff saved-pumps pumps --json > pumps-upgrade.json
```

The report separates compiled contract changes from source, version, compiler,
and dependency identity changes. It reads metadata without importing either
package. Both versions must use the current compiler's metadata formats.
Differences return exit status zero; invalid or missing metadata returns status
two. Review and validation decide whether an update is acceptable.

Generation is deterministic. Compiling unchanged input gives byte-identical
output, so ontology changes show up as reviewable diffs.

## Extension annotations

An extension names the installed package it builds on:

```turtle
@prefix ex: <urn:example:pumps#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix codegen: <https://watermetadata.org/plumb/codegen#> .

ex: a owl:Ontology ;
    owl:imports <https://watermetadata.org/ontology/watr> ;
    codegen:baseModule "plumb.watr" .
```

| Annotation | Purpose |
| --- | --- |
| `codegen:baseModule` | Installed Python package that provides the base classes |
| `codegen:projection codegen:PropertySchema` | Export a node shape as a property schema |
| `codegen:pythonName` | Explicit Python name for a class or field |
| `codegen:localName` | RDF local name for a property, independent of its Python keyword |

Annotations choose names and projections. Requirements stay in SHACL.

## Classes and properties

| Ontology | Generated Python |
| --- | --- |
| `owl:Class` / `rdfs:Class` | class |
| `rdfs:subClassOf` | Python inheritance, so `isinstance` follows subsumption |
| `rdfs:label`, `skos:definition` / `rdfs:comment` | `meta` and docstrings |
| property with `rdfs:domain` or `schema:domainIncludes` | attribute on the domain class |
| `sh:minCount >= 1` | required keyword argument |
| `sh:maxCount 1` | single-valued attribute; otherwise a collection |
| `sh:class`, `sh:datatype`, `rdfs:range` | type annotation and runtime check |
| `sh:hasValue` | required value; for a collection, a required member |
| `sh:defaultValue` | replaceable default on new objects |
| `sh:in` | allowed choices |
| `owl:inverseOf` | inverse kept in sync |
| `owl:equivalentProperty` | merged into the ontology's primary namespace |

An extension class has one constructive parent, which may be another class
in the same extension. Contradictory bounds, defaults, or inherited choices are
reported during compilation. Loading a graph preserves it as written: it
does not fill in missing defaults or required values.

Constraints the compiler cannot turn into constructor checks, such as complex
paths, still apply at `validate()` time, because validation uses the original
shapes.

## Named connection points

A named point is a qualified shape over `s223:hasConnectionPoint` with:

- an `sh:name`, which becomes the Python attribute, such as `inlet` or
  `feed_water`;
- an inlet, outlet, or bidirectional `sh:class`;
- an exact `sh:hasValue` medium and equal positive qualified minimum and
  maximum counts;
- distinguishing facts, such as a fixed `rdfs:label`, when several points
  share a direction and medium.

```turtle
dw:ClarificationStageShape a sh:NodeShape ;
    sh:targetClass dw:ClarificationStage ;
    sh:property [ sh:path s223:hasConnectionPoint ; sh:name "sludge" ;
        sh:qualifiedMinCount 1 ; sh:qualifiedMaxCount 1 ;
        sh:qualifiedValueShape dw:Sludge ] .
dw:Sludge sh:class s223:OutletConnectionPoint ;
    sh:property [ sh:path s223:hasMedium ; sh:hasValue watr:Fluid-Sludge ],
        [ sh:path rdfs:label ; sh:hasValue "sludge" ] .
```

One point becomes a `PointRef`; a group becomes a `PointGroupRef`. Pass them to
`connect()`, and look up the concrete point with `resolved.point(ref)`. When a
graph is loaded, the point's RDF facts identify it again; if they match more
than one point, loading raises an error.

Nested `sh:and`, `sh:or`, and `sh:xone` shapes over connection points are kept
as solver constraints. `sh:or` values on `hasMedium` become medium domains.

## Property schemas

Mark a node shape with `codegen:projection codegen:PropertySchema`. Each field
is a property shape over `s223:hasProperty` with:

- a stable `sh:qualifiedValueShape` IRI;
- a qualified minimum and maximum count of one;
- a readable `sh:name`, which becomes the field name.

The value shape supplies the property class, the numeric `hasValue` datatype,
the QUDT quantity kind, the unit, and medium, substance, and aspect
constraints. Shapes can be reused through `sh:node` and `sh:and`.

```turtle
ex:PressureDesignShape a sh:NodeShape ;
    codegen:projection codegen:PropertySchema ;
    codegen:pythonName "PressureDesign" ;
    sh:property [ sh:path s223:hasProperty ; sh:name "pressure" ;
        sh:qualifiedMinCount 1 ; sh:qualifiedMaxCount 1 ;
        sh:qualifiedValueShape ex:Pressure ] .
ex:Pressure sh:class s223:QuantifiableProperty ;
    sh:property [ sh:path s223:hasValue ; sh:datatype xsd:double ;
                  sh:minCount 1 ; sh:maxCount 1 ; sh:minInclusive 0.0 ],
        [ sh:path qudt:hasQuantityKind ; sh:hasValue kind:Pressure ],
        [ sh:path qudt:hasUnit ; sh:defaultValue unit:PA ;
          sh:in (unit:PA unit:KiloPA unit:BAR) ],
        [ sh:path s223:hasAspect ; sh:hasValue s223:Aspect-Nominal ] .
```

| Shape | Field behaviour |
| --- | --- |
| `xsd:double`, `xsd:float`, `xsd:decimal` | accepts a Python number |
| `sh:defaultValue` on `hasValue` | default value; otherwise required |
| `sh:minInclusive`, `sh:maxInclusive`, `sh:in` | checked on construction |
| `sh:defaultValue` on `hasUnit` | unit for bare numbers |
| `sh:in` on `hasUnit` | allowed units for a `QuantityAmount` |
| `sh:hasValue` on `hasUnit` with a single unit | fixed unit |
| fixed `rdfs:label` | preserved, and distinguishes fields with the same quantity kind |
| `skos:notation` | shown by `describe()`, such as `S_NH4` |

Fields are scalar. Units are checked against the QUDT dimension vector when a
value is created, and an unknown compatibility is an error rather than a
guess. No unit conversion takes place.

## Names

- Classes keep their IRI local name: `Air_Handling_Unit` stays as it is.
- Properties use the snake-case local name: `hasPoint` becomes `has_point`.
- A few S223 point predicates have shorter names: `hasMedium` is `medium`,
  `isConnectionPointOf` is `owner`, `connectsThrough` is `connection`, and
  `pairedConnectionPoint` is `paired_with`.
- Names that collide with the object API (`name`, `type`, `label`, `comment`,
  `meta`, `model`, `contains`, `ports`, `describe_ports`) or with Python
  keywords get a trailing `_`.
- Different IRIs with the same name get `_2`, `_3`, and so on, in sorted IRI
  order. A deprecated term is suffixed before a current one. WaTr reuses
  unchanged S223 imports and provides typed views for added authoring surfaces;
  `watr.Pump` is a view of `s223.Pump` with the same ontology IRI.
- Enumeration values are under `enums.values` with flat names (`Fluid-Water`
  becomes `Fluid_Water`), and under their branch for completion, such as
  `enums.Substance.Medium.Mix.Fluid.Water`.

## What the compiler does not do

The compiler projects the constructive part of SHACL into Python. It is not a
general SHACL-SPARQL engine. Complex paths, disjunctive layouts outside
connection points, and parents that the extension does not link produce
diagnostics. Full validation always uses the original shapes, including the
constraints the projection leaves out.
