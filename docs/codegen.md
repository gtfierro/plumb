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

The internal `gen/s223.py` adapter recognizes connection semantics by exact
vocabulary IRI and RDF ancestry. Custom point subclasses keep their direction
through Python alias changes. Unrelated predicates named `hasConnectionPoint`,
`hasMedium`, or `inverseOf` do not acquire S223 meaning. Expressions containing
validation-only boolean branches are excluded from solver assertions and
candidate restrictions; full SHACL validation remains authoritative.

Every ontology and configuration package carries `_support.json`. Its source
inventory distinguishes constructor, runtime, solver, and validation checks;
it also records policy bindings, connection expressions, and quantity projections.
Each constraint names its target, source shape, path, and parameter. A summary
counts the enforcement categories and missing optional bindings. Descriptions
identify approximations, such as Python type checks that leave exact RDF
datatype validation to SHACL.
Anonymous source identifiers name content/context groups; target and path retain
their scope when equivalent anonymous RDF nodes have interchangeable labels.

This makes omitted qualifiers visible: the paired-point qualifier on heat
exchangers remains in SHACL validation rather than becoming an unconditional
medium/count requirement. Unsupported constructive forms fail with source-linked
errors. The report replaces the earlier connection-only report.

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
parents pruned. Direct RDF edges and transitive ancestry are emitted separately
from Python bases. `Class.meta.parents`, hierarchy discovery, and
`Class.meta.is_a(parent)` use that semantic metadata. Runtime range checks keep
accepting legitimate ontology subtypes even when Python cannot inherit every
parent.

## Effective property constraints

Generated packages export `_symbols.json`, a versioned description of
ontology identity, semantic ancestry, effective properties, enums, and port
constraints. The compiler can read this export without importing generated
Python modules. Missing or incompatible exports identify the dependency and
require regeneration rather than falling back to runtime registry inspection.
Configuration compilation consumes these symbols rather than installed Python
classes. Exports record dependency digests and defining modules, including through
chains of extensions; a stale dependency must be regenerated before reuse.

Both front ends use the same property refinement and Python descriptor renderer.
`sh:hasValue` members accumulate, `sh:in` lists intersect (an empty list permits
no values), and a more specific `sh:defaultValue` replaces an inherited default.
An inherited default that falls outside a narrowed choice set fails compilation.
RDF constants retain their lexical/datatype form in dependency metadata.

The shared compiler composes property constraints over the RDF parent graph
before selecting Python bases. Repeated declarations and inheritance intersect
their counts (`max(minCount)`, `min(maxCount)`); contradictory bounds fail with
the predicate and source shapes. Required constructor arguments enforce the
numeric minimum. Cyclic object requirements can defer constructor enforcement
while preserving their semantic minimum in metadata and bundled SHACL.
Minimum counts are checked at constructor completion and during graph validation;
edits may temporarily remove an endpoint while a connection is rerouted. Mutation
checks enforce ranges, upper bounds, fixed members, and finite choices atomically.

Ranges retain conjunctions separately from explicit `sh:or` alternatives.
Runtime checks enforce every group. An annotation uses the known narrower
range where possible; otherwise one conjunct is a conservative approximation
because Python lacks general intersection types. The compiler includes semantic
subtypes omitted by MRO repair in annotations and materializes inherited
descriptors that Python would otherwise lose.

Predicate identity precedes naming: distinct predicates with the same Python
name receive distinct suffixes. Equivalent predicates still share their chosen
canonical IRI. Collection mutations validate the complete change, including
maximum counts and inverse links, before changing the model.

## UX overlays

Operator sugar and containment rules are *policy*, not ontology fact, so they
live in overlays (`plumb/gen/overlays.py`), keyed by ontology name. Bindings accept
IRIs or generated names; S223/WaTr built-ins use IRIs so Python alias changes
cannot redirect them. Targets are required by default. Missing required targets
or incompatible bindings fail before writing files, with structured
`CompilationError.diagnostics`. A missing optional target is recorded in the
support report and omitted; an incompatible target remains an error.

```python
from plumb.gen.overlays import Binding, Overlay

policy = Overlay(
    rshift={"urn:example#Equipment": "urn:example#feeds"},
    sensor_classes={
        "http://qudt.org/vocab/quantitykind/Temperature":
            Binding("urn:example#TemperatureSensor", required=False),
    },
)
```

Pass `--no-overlay` to disable built-in registrations, or supply an `Overlay`
to ontology compilation. Configurations inherit their base package's policy;
custom configuration overlays are rejected instead of silently ignored.

## Imported-class profiles

A configuration can target an imported class with a SHACL shape. It keeps the
dependency's exact Python class and enum objects; constraints on imported classes
are enforced by model validation. They appear with `profile: true` and
`enforcement: ["validation"]` in `_support.json`, and their targets are listed in
`profile_targets`. Complex paths and boolean expressions remain in SHACL.

Profiles do not mutate canonical constructors or install properties on dependency
classes. Imported constructor defaults, renamed Python classes, and added
ancestry fail compilation with the affected target. Declare a local subclass
when a separate constructive Python projection is needed.

Authored extension instances select their package's shapes automatically.
`Model.from_graph(..., registries=...)` also retains explicitly selected profiles
when every instance has an imported class. Dependency profiles compose by
conjunction and survive resolution. Canonical class-valued links resolve local
extension terms without changing the dependency's registry.

See the [identity/profile decision](shared-identities-and-profiles.md) for the
tested prototype and why the actual WaTr migration remains a separate step.

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
