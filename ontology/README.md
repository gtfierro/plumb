# Local WaTr ontology snapshot

`asm2d.ttl` defines the ASM2d equipment configurations, named ports, property
groups, defaults, units, and split bases in RDF and SHACL. Regenerate its Python
package with `make regen`. See
[the extension compiler reference](../docs/book/reference/extension-compiler.md). `asm2d-components.ttl`
adds the component pools used by the WaTr base package.

`seawater-ro.ttl` defines reusable RO and pretreatment process configurations,
branched port layouts, and quantity schemas for feed, membrane, pumps, storage,
pressure recovery, permeate pressure, and UV. `hvac.ttl` defines the air/water
cooling coil shared by the S223 examples.

`drinking-water.ttl` defines a conventional surface-water treatment train using
WaTr coagulation, flocculation, sedimentation, sand filtration, and chlorination
equipment and processes. Its stage configurations include separate sludge and
filter backwash ports. The sequence follows
[CDC's treatment overview](https://www.cdc.gov/drinking-water/about/how-water-treatment-works.html);
the port layouts are this repository's teaching configuration. All four domain
packages regenerate offline with `make regen`.

`qudt-catalog-extras.ttl` supplies additional reference terms to the locked
QUDT catalog projection. All regeneration uses `sources.lock.json` and the
[documented snapshots](snapshots/README.md). The lock captures the existing
WaTr validation imports separately from the QUDT 3.4.0 reference catalog.

`watr-0.3.0rc1.ttl` archives the unmodified `watr.ttl` asset of WaTr
[v0.3.0.rc1](https://github.com/DataDrivenCPS/water-ontology/releases/tag/v0.3.0.rc1)
(SHA-256 `9107996edff06fdfc7d7af524eedf51ca2837d72e6df03ffe5b21d45dda18110`).
It keeps the unversioned ontology IRI and `owl:versionInfo "0.3.rc1"`.
Compilation now uses the locked closure snapshot instead of resolving this
asset's imports from the network.

The release states which subjects and objects `watr:hasProcess` and
`watr:hasTreatmentObjective` accept with SHACL target shapes
(`watr:ProcessBearerShape`, `watr:ProcessValueShape`, and
`watr:TreatmentObjectiveValueShape`). The compiler reads those shapes as the
properties' domains and ranges, so the generated package exposes
`has_process` and `has_treatment_objective` on equipment and systems without
local additions to the ontology. Their values are punned process and objective
class terms, passed as generated Python classes and serialized as ontology
IRIs.

Regenerate and check all supported packages offline:

```bash
make regen
make regen-check
```

See [snapshot provenance and source updates](snapshots/README.md) before
updating ontology inputs.
