# Code generation

plumb is a compiler: ontology + SHACL in, ordinary Python modules out.
Generated packages are real code (not stubs, not runtime metaclasses), so
editors, type checkers, and debuggers see exactly what runs.

The command line, extension annotations, the ontology-to-Python mapping, and
the naming rules are user documentation, in the book's
[extension compiler reference](book/reference/extension-compiler.md). This page
covers the compiler's internals and regenerating the committed packages.

## Solver translation boundary

SHACL Core connection-point structure compiles directly to Z3. Constraints
that exist only as SHACL-SPARQL remain validation-only.

Media likelihood comes from the ontology's permitted-media domains, not a
class-specific preservation flag. For every pair of active ports on an entity,
the optimizer adds an affinity preference only when their compiled domains
overlap. Extension authors therefore influence assignment by publishing
accurate `hasMedium` constraints on qualified ConnectionPoint shapes. Hard
equality exists only across the two endpoints of a Connection, between paired
ports, and across `mapsTo`. A point that a part's point maps onto drops its
own class's medium domain, since a container's shapes describe its own
points: an AHU's chilled-water port takes the coil's medium, not air. Mapped
points are solved in one component and must share a direction.

The `connection_classes` overlay mapping is separate: it maps a resolved
medium or ancestor to the resource to materialize, such as `Fluid-Water` →
`Pipe`. Model authors can add instance-level evidence with `medium=`,
`handle.medium`, or authored ConnectionPoints as described in
[Connect equipment](book/how-to/connect-equipment.md).

One SHACL-SPARQL constraint is translated by hand: 223P's "Incompatible
Medium" rule, which requires a property's `ofMedium` to be compatible with its
host's `hasMedium`. The generator emits each medium's constituents
(`EnumValue.constituents`), `EnumValue.compatible_with()` implements the
rule's four cases, and the solver constrains each pipe's and point's medium
by the properties attached to it. Resolution then fills in `ofMedium` where
it is missing.

**Final solver TODO:** implement a bounded SHACL-SPARQL-to-Z3 translator for
basic graph patterns, equality/inequality, `EXISTS`/`NOT EXISTS`, `UNION`,
subclass paths, and constituent-medium compatibility. Unsupported queries
must remain validation-only. Translated constraints must also distinguish hard
requirements from ranking evidence.

## Inheritance repair (MRO)

RDF permits parent combinations Python's C3 linearization rejects. At
generation time each parent tuple is repaired: redundant ancestors dropped,
parents ordered most-derived-first, and — only if C3 still fails — trailing
parents pruned. Pruned links remain visible through `meta.iri`/RDF; they just
don't contribute to the Python MRO.

## UX overlays

Operator sugar and containment rules are *policy*, not ontology fact, so they
live in overlays (`plumb/gen/overlays.py`), keyed by ontology name. An
overlay entry that doesn't resolve against a given ontology version is
skipped with a comment in the generated file, so one overlay can serve many
versions. Pass `--no-overlay` to disable, or supply your own
`Overlay` via the Python API (`plumb.gen.compile_source`).

## Regenerating the committed packages

```bash
uv run python scripts/generate_brick.py
uv run pytest tests/test_brick.py
```

The Brick script bundles its imports through ontoenv. S223, WaTr, QUDT, and
the example domain packages instead use locked local inputs:

```bash
make regen
make regen-check
```

`scripts/regenerate.py` verifies the SHA-256 of each input recorded in
`ontology/sources.lock.json`, builds in a temporary source tree, and publishes
only after every package compiles. Configurations link against the freshly
built base packages. `_generated.json` records owned files, so removed output
is cleaned up without touching handwritten files or nested packages.
`_build.json` records input provenance. The check command compares both file
sets and bytes and runs in CI.

Generation never fetches sources or follows network imports. The starting
inputs are captured closure snapshots and a recovered vocabulary projection;
see [snapshot provenance](../ontology/snapshots/README.md). Source updates are
explicit: acquire and review documents, record their identities, versions,
imports, and hashes in the lock, regenerate, then review the changes.

Base-package generation relabels blank nodes from their content and sorts the
input triples, so output is independent of input assembly order. The original
WaTr release asset remains archived in `ontology/watr-0.3.0rc1.ttl`; current
compilation uses the locked complete closure, including local component pools.
