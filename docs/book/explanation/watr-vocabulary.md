# The WaTr vocabulary

`plumb.watr` is generated from WaTr
[v0.3.0.rc1](https://github.com/DataDrivenCPS/water-ontology/releases/tag/v0.3.0.rc1),
vendored unmodified as `ontology/watr-0.3.0rc1.ttl`. Terms may change before
0.3.0.

## Equipment, process, objective, and role

Each answers a different question about a unit:

| Question | Relation | Example |
| --- | --- | --- |
| What is it? | `rdf:type` | `watr:GravityThickener` |
| What does it do? | `watr:hasProcess` | `watr:Process-Settling` |
| What is it for? | `watr:hasTreatmentObjective` | `watr:TreatmentObjective-Thickening` |
| What is its place in this system? | `s223:hasRole` | `watr:Role-Primary` |

A sedimentation tank and a gravity thickener share a process, settling, but
not an objective: one clarifies water, the other thickens sludge. A role
depends on the installation.

Processes and objectives are classes, used directly as values; they serialize
as class IRIs. Roles are enum values. See
[Set processes, objectives, and roles](../how-to/watr-processes.md).

## Class defaults

Some processes and objectives follow from the equipment class: every
`GravityThickener` settles to thicken. WaTr's `ClassDefaultsRule` infers these
in RDF, and generated constructors apply the same defaults. A default is
skipped when you supply that term or a subclass of it.

| Where | Defaults applied |
| --- | --- |
| Python constructor | most specific term only |
| `ClassDefaultsRule` (`validate()`, or `from_graph(infer=True)`) | every implied term |
| `from_graph()` without `infer` | none; the graph is kept as written |

`ProcessObjectiveRule` adds the objective a process implies
(`Process-Chlorination` implies disinfection). It runs only as a SHACL rule.
No rule supplies a role.

## Media and constituents

WaTr models freshwater with an H₂O constituent, and seawater, brackish water,
and brine with H₂O and NaCl. A shared constituent makes media compatible at a
connection. It does not assert equal composition.

`Fluid-Sludge` is a `Mix-Fluid` of water and solids, not a kind of
`Fluid-Water`, so a sludge port does not accept a water-only connection.

The bundled shapes also check percentage compositions:

- `CompositionPercentageShape` flags constituent percentages that exceed
  100%.
- `CompositionComplementRule` infers a single missing percentage from the
  rest.

## Names shared with S223

`plumb.watr` contains the S223 classes it imports as well as WaTr's own.
When both define a name, WaTr's keeps it and S223's gets a suffix: `Pump` is
`watr:Pump` and `Pump_2` is `s223:Pump`. WaTr's pump accepts any `Mix-Fluid`,
including sludge; S223's admits only water, oil, or refrigerant. Check
`Pump.meta.iri` when it matters.

Unchanged imports share the exact S223 object: `watr.Pipe is s223.Pipe`.
When WaTr adds properties or profile ancestry, it provides a typed Python
subclass whose `meta.canonical` points to the original S223 class. These views
work in S223 property ranges without changing S223's classes or constructors.
`Pump_2` carries WaTr's added Pump parent edge; its canonical S223 base retains
the original ancestry.

WaTr's enum additions, such as `Fluid_Sludge` and `Role_Backwash`, sit
alongside the S223 values in `plumb.watr.enums`.
