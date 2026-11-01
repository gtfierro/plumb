# plumb — Design

plumb compiles ontology and SHACL sources into ordinary typed Python packages
for building and water models. The ontology describes meaning and constraints;
a small runtime supplies authoring, querying, resolution, and RDF interchange.
The supported API is documented in the [book](docs/book/index.md); implementation
ownership is mapped in [architecture](docs/architecture.md).

## Deep modules with simple interfaces

The compiler owns loading, normalization, linking, domain adaptation, emission,
and diagnostics behind `generate(...)` / `plumb gen`. Model authors use generated
classes and `Model.check()`, `resolve()`, and `compile()`. They do not coordinate
passes, reconcile registries, or choose a solver backend.

Give each invariant one owner. General constraint composition belongs to the
compiler, model lifecycle belongs to core, and vocabulary interpretation belongs
to internal domain adapters. An abstraction should hide knowledge and remove
caller decisions. Do not add a framework extension point merely to distribute
implementation across more files. Coherent interfaces take priority over
backward compatibility with earlier generated APIs.

## Compile ahead of time

```text
locked documents + import closure + authoring policy
                         |
              shared semantic normalization
                         |
       linked classes, effective constraints, diagnostics
                         |
           ordinary Python + bundled RDF + exports
                         |
          core runtime + optional domain planning
```

Generated packages contain real classes, signatures, descriptors, and metadata,
so editors and static checkers see the same authoring surface that executes.
Handwritten policy belongs in compiler overlays or adapters. Generated files
are replaced by regeneration, not patched by hand.

Committed S223, WaTr, QUDT, and domain configurations use verified local inputs
from `ontology/sources.lock.json`. Ordinary generation never retrieves new
sources. Historical closures are labelled as snapshots rather than attributed
to an unverified upstream release. A staged build completes every package before
publishing, and an ownership manifest removes stale generated files safely.
Brick remains a runtime regression target with its separate generation script.

## Semantic constraints precede Python projection

IRI identity comes before Python naming. The compiler composes property
constraints conjunctively over RDF ancestry: numeric bounds intersect, required
values accumulate, finite choices intersect, and inherited defaults must remain
valid. Explicit alternatives remain alternatives. Equivalent predicates are
merged deliberately; unrelated naming collisions receive deterministic suffixes.

RDF parent edges and transitive ancestry remain available independently of
Python bases. C3 repair cannot discard semantic ancestry or constraints, and
cycles fail compilation. Python annotations conservatively approximate
intersections where needed; runtime metadata retains all supported groups.
Constructor deferral for cyclic or staged authoring does not erase graph
minimum counts. Ranges, upper bounds, fixed values, and finite choices are
checked before mutation; graph validation remains authoritative.

Base ontologies and configurations share property normalization and rendering.
Configuration-specific named points and scalar property schemas remain explicit
projections. The compiler does not claim arbitrary SHACL constructive support:
each constraint is compiled, retained for validation with an explicit support
status, or rejected with a source-linked diagnostic.

## Shared identities and explicit views

Compiler dependencies are versioned data exports with pinned digests, not
runtime registry introspection. Linking never executes the dependency's Python
package. Missing exports, incompatible identities, and stale dependencies fail
with regeneration guidance.

WaTr reuses unchanged S223 class and enum objects. Where WaTr adds properties,
ancestry, or authoring policy, it provides a nominal typed view with the same
ontology IRI and `meta.canonical` identifying the dependency class. Model-scoped
profiles enforce additional validation constraints without mutating canonical
constructors. Registry composition selects views and schemas deterministically,
including for hydration and class-valued links. See the
[identity/profile decision](docs/shared-identities-and-profiles.md).

## Authoring and model lifecycle

An authored `Model` is mutable. Generated constructors bind entities to the
ambient model, validate supplied values, initialize domain declarations, and
attach containment. Descriptors own typed relationships and inverse maintenance.
Core transactions restore existing links, names, revisions, and caches when a
compound authoring operation fails.

`check()` reports deferred decisions without changing authored objects.
`resolve()` plans, copies the model into an isolated build, applies domain
results, and publishes an immutable snapshot. A failed build is discarded.
Core owns cloning, revision tracking, bounded plan caching, and publication;
the S223 backend supplies a report and an operation that populates domain
objects. Unchanged sparse components reuse plans across unrelated edits.

Ordinary RDF models and already concrete loaded graphs do not invoke the native
planner. Loaded graph copies preserve original IRIs, unprojected RDF, schema
selection, and named-point references. Authoring edits invalidate cached
snapshots while previously published snapshots and explanations remain stable.
`graph()` and `save()` serialize resolved state. `compile()` also runs SHACL
validation by default.

## Domain meaning and authoring policy

The internal S223 adapter recognizes vocabulary by exact IRI and semantic
ancestry. WaTr shares its connection semantics. Qualified point shapes supply
counts, directions, and medium domains; supported boolean expressions retain
structure. Unknown branches stay in validation and cannot silently become true
or false solver constraints. SPARQL-only constraints remain validation-only
apart from the explicitly implemented medium/property compatibility rule.

The runtime domain capability owns point authoring/restoration, boundaries,
systems, endpoint ownership, and topology. Z3 planning partitions deferred
intentions, solves hard requirements, ranks permitted assignments, checks
uniqueness, and explains decisions. Explicit media and named points disambiguate
connections. Brick connection operators instead use their configured ordinary
relationship. Containment, operator aliases, and medium-to-connection-class
selection are explicit authoring policy, separate from ontology facts.

Property schemas create independent RDF properties on equipment, points, or
connections. Units and quantity kinds come from the compiled QUDT catalog;
unit compatibility is checked without implicit conversion. Model hydration
restores observable facts rather than applying authoring defaults or fabricating
missing constructive values.

## Reviewable ontology evolution

`plumb diff BEFORE AFTER` compares saved generated package directories without
executing either version or loading historical dependencies. It separates
compiled contracts and enforcement from source/build/dependency provenance.
Anonymous constraint fingerprints preserve query and list changes without
making blank-node labels part of the public contract. The report supports human
review; it does not certify compatibility or prove arbitrary SHACL equivalence.

The [upgrade workflow](docs/ontology-upgrades.md) explains source acquisition,
lock updates, semantic review, regeneration, and verification. Evolution tests
exercise supported source changes through generated typing, positive/negative
validation, mixed S223/WaTr connections, serialization, and hydration. RDF
isomorphism checks complement byte comparisons after fresh parsing and reordered
input. CI runs the full semantic suite and offline regeneration gate.

The [hardening plan](docs/compiler-hardening-plan.md) records the completed
implementation sequence. Future work, including BuildingMOTIF templates,
source-fact traceability, blank-node authoring, and WaterTAP translation, belongs
in the [roadmap](docs/roadmap.md). These are not promises of current support.
