# Generate a domain API

Write equipment and property sets in RDF and SHACL, then compile them into a
Python package. [Domain extensions](../explanation/domain-extensions.md)
explains when to.

## Write the extension

Save this as `pumps.ttl`. `codegen:baseModule` names the installed package it
extends. It defines a supply pump with named water ports and a pressure
property set.

```turtle
@prefix ex: <urn:example:pumps#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix s223: <http://data.ashrae.org/standard223#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix qudt: <http://qudt.org/schema/qudt/> .
@prefix kind: <http://qudt.org/vocab/quantitykind/> .
@prefix unit: <http://qudt.org/vocab/unit/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix codegen: <https://watermetadata.org/plumb/codegen#> .

ex: a owl:Ontology ;
    owl:imports <http://data.ashrae.org/standard223/1.0/model/all> ;
    codegen:baseModule "plumb.s223" .

ex:SupplyPump a owl:Class ; rdfs:subClassOf s223:Pump .
ex:SupplyPumpShape a sh:NodeShape ; sh:targetClass ex:SupplyPump ;
    sh:node ex:PressureDesignShape ;
    sh:property [ sh:path s223:hasRole ; sh:hasValue s223:Role-Supply ],
        [ sh:path s223:hasConnectionPoint ; sh:name "inlet" ;
          sh:qualifiedMinCount 1 ; sh:qualifiedMaxCount 1 ;
          sh:qualifiedValueShape ex:Inlet ],
        [ sh:path s223:hasConnectionPoint ; sh:name "outlet" ;
          sh:qualifiedMinCount 1 ; sh:qualifiedMaxCount 1 ;
          sh:qualifiedValueShape ex:Outlet ],
        [ sh:path s223:hasConnectionPoint ; sh:minCount 2 ; sh:maxCount 2 ] .
ex:Inlet sh:class s223:InletConnectionPoint ;
    sh:property [ sh:path s223:hasMedium ; sh:hasValue s223:Fluid-Water ],
        [ sh:path rdfs:label ; sh:hasValue "inlet" ] .
ex:Outlet sh:class s223:OutletConnectionPoint ;
    sh:property [ sh:path s223:hasMedium ; sh:hasValue s223:Fluid-Water ],
        [ sh:path rdfs:label ; sh:hasValue "outlet" ] .

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

- `sh:hasValue` adds a required member; other values are still allowed.
- `sh:defaultValue` sets a replaceable default.
- `sh:in` lists the allowed choices.
- Each named port needs a fixed direction, medium, and count. The fixed
  labels tell the two water ports apart.

The [extension compiler reference](../reference/extension-compiler.md) lists
every rule.

## Compile it

```bash
plumb gen --file pumps.ttl --name Pumps --out pumps
```

## Use it

```python
from plumb import Model
from plumb.qudt import QuantityAmount as Q, units
from pumps import SupplyPump, PressureDesign

with Model("urn:example:plant#") as model:
    pump = SupplyPump("pump")
    pump.apply_properties(PressureDesign(pressure=Q(7.0, units.BAR)))

assert model.validate().ok
```

A bare pressure uses Pa, the source default. Validation uses the package's
bundled shapes.

## Load saved models

`from_graph()` only detects the bundled extensions. Pass your registry:

```python
from plumb import Model
import pumps

model.save("plant.ttl")
loaded = Model.from_graph("plant.ttl", registries=pumps.REGISTRY)
assert isinstance(loaded["pump"], SupplyPump)
```

The registry includes the base classes. See
[Save, load, and edit models](save-and-load.md) for how registries are chosen.

## Regenerate the bundled packages

The sources are `ontology/drinking-water.ttl`, `asm2d.ttl`,
`seawater-ro.ttl`, and `hvac.ttl`:

```bash
make regen
```
