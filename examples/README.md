# Examples

Examples are grouped first by ontology and then by scenario. Each scenario
directory contains its runnable Python and related inputs or generated RDF.

## Brick

- [`brick/quickstart/`](brick/quickstart/) — a small building, HVAC equipment,
  zones, points, and Brick `feeds` relationships.

## ASHRAE 223P

- [`s223/ahu/`](s223/ahu/) — an air handler using a SHACL-generated coil
  configuration, exporting its instance graph and ontology schema.
- [`s223/cooling_coil/`](s223/cooling_coil/) — an imported air/water coil
  configuration with four named ports and fixed media.

## WaTr

- [`watr/treatment/`](watr/treatment/) — conventional surface-water treatment:
  coagulation, flocculation, clarification, sand filtration, and chlorination,
  with separate sludge and backwash boundaries.
- [`watr/asm2d/`](watr/asm2d/) — the ASM2d treatment train with generated
  equipment configurations and typed feed/design schemas.
- [`watr/seawater_ro/`](watr/seawater_ro/) — a full seawater reverse-osmosis
  system using generated configurations and immutable quantity schemas.
- [`watr/seawater_ro_pretreatment/`](watr/seawater_ro_pretreatment/) —
  seawater pretreatment stages.
- [`watr/epanet_anytown/`](watr/epanet_anytown/) — the Anytown EPANET input,
  converter, generated WaTr graph, and a directly authored topology example.
- [`watr/distribution_network/`](watr/distribution_network/) — a small,
  directly authored distribution loop with hydraulic and water-quality
  sensors.

Reusable configurations and value schemas come from RDF and SHACL in
[`ontology/`](../ontology/). Model authors import them from
`plumb.s223.hvac`, `plumb.watr.asm2d`, `plumb.watr.seawater_ro`, or
`plumb.watr.drinking_water`. Regenerate the packages after editing their sources:

```bash
make regen
```

The EPANET converter supplies explicit units with `QuantityAmount` for source
values. Monitoring examples describe observable properties without inventing
sample readings. Brick's `feeds` examples retain their ontology's direct edges.
