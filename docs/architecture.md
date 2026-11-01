# Architecture

```
user script
    │  plain typed Python                     existing RDF graph
    ▼
generated package (plumb.brick, ...)      ← output of plumb.gen
    │  classes, PropertySpecs, registries          │
    │                                              ▼
    │                                      query hydration (core/query.py)
    ▼
runtime core (plumb.core)
    │  Entity / Model / descriptors / deferred intentions
    ▼
core lifecycle + optional domain plan (S223: plumb.solver223)
    │  core-owned immutable snapshot
    ▼
rdflib (serialization) · shifty (SHACL) · ontoenv (imports resolution)
```

## Runtime core (`src/plumb/core/`)

- **`meta.py`** — the data generated code instantiates: `OntologyInfo`,
  `PropertySpec` (one attribute: predicate, kind, ranges, cardinality,
  inverse), `ClassInfo` (per-class provenance), and the per-package
  `Registry` that resolves string range names to classes at runtime.
- **`entity.py`** — the `Entity` base. Construction binds to the ambient
  `Model`, applies constructor kwargs through descriptors, enforces required
  properties, then attaches to any open containment scope. Core transactions
  roll back failed construction, including inverse links, names, and caches.
  `.meta` serves `ClassMetaView` /
  `InstanceMetaView`. `>>`/`<<` read the class's `_RSHIFT` property.
- **`relations.py`** — descriptors covering object relations, literals,
  enumeration values, compiled vocabulary terms, and unconstrained scalar
  values. `ValueOne` implements predicates such as S223 `hasValue`, accepting
  either a Python literal or named RDF resource without forcing a wrapper
  node. Descriptors enforce semantic range intersections and counts even where
  Python annotations can only approximate them. Collection updates preflight
  the whole change, including inverse edges, before modifying either store.
- **`containment.py`** — the ambient `with` stack (a `ContextVar`) plus the
  per-package `ContainmentTable`; `attach()` walks the stack innermost-first
  and applies the first matching rule, raising with guidance otherwise.
- **`model.py`** — namespace, IRI minting, name uniqueness, entity lookup,
  revision tracking, bounded plan caching, serialization, and transactions.
  It also exposes typed selection and tracked mutation over loaded
  graphs.
  Serialization and validation of authored models operate on resolved
  snapshots; output graphs declare an `owl:Ontology` and import the generated
  packages and compiled vocabularies they reference.
- **`query.py`** — optionally runs shifty inference, chooses the most-specific
  generated class for each typed RDF resource, and hydrates generated
  attributes. Generated attribute changes replace their managed triples while
  unmodeled RDF is preserved.
- **`lifecycle.py`** / **`snapshot.py`** — select an optional domain plan,
  translate resolution failures, copy model state, and publish a frozen snapshot.
  Plain RDF models take the copy path without loading the native planner. Copies
  preserve loaded IRIs, unprojected RDF, selected schemas, and point references.
  A failed domain build is discarded; it cannot publish a partial snapshot.
- **`traversal.py`** — the `find`/`find_all` filter semantics (narrowing
  classes and enum values, `exact()`), containment navigation over the
  registries' containment tables, and delegation of topology walks to the
  registry's domain capability. Indexes are cached on the model and dropped
  by every edit. See [traversal.md](traversal.md).
- **`resolution.py`** — stable authored `ConnectionHandle`s, staged generated
  property collections, and the `ResolutionReport`/`ResolvedModel` public API.
- **`validation.py`** — runs shifty, then translates the standard SHACL
  report graph into `Issue`s that reference entities and attribute names.

Design invariant: **user-facing errors speak Python** (class names, attribute
names, entity names), and where the fix is mechanical the message contains
the exact code to write.

## Compiler (`src/plumb/gen/`)

The compiler hides normalization, domain interpretation, and Python lowering
behind `generate(...)` / `plumb gen`. These are internal responsibilities:

1. **`schema.py`** — collects classes and composes effective property constraints
   over semantic RDF ancestry before selecting Python bases. Predicate identity
   precedes Python naming. **`ir.py`** holds the private representation shared
   by normalization, domain adapters, and rendering.
2. **`constraints.py`** — common conjunctive property traversal and cardinality
   normalization for ontology and configuration front ends. Range groups preserve
   conjunctions separately from alternatives.
3. **`s223.py`** — the internal S223 semantic adapter, also used by WaTr. Exact
   predicate IRIs and ontology ancestry select connection slots and directions;
   nested medium constraints compose by intersection. Unknown boolean branches
   remain validation-only.
4. **`emit.py`** — a renderer of the IR. Emits aliased runtime imports
   (so ontology names like RealEstateCore's `Entity` can't shadow the base),
   specs, classes with docstrings from the ontology text, and explicit typed
   `__init__` methods wherever a class changes the property set.
5. **`overlays.py`** — resolves authoring policy targets once, by IRI or generated
   name, with required/optional binding diagnostics. The emitter renders resolved
   registrations without re-interpreting policy. **`diagnostics.py`** emits the
   shared source inventory and enforcement report for both front ends.

`sources.py` verifies locked local inputs. `scripts/regenerate.py` stages an
offline build of S223, WaTr, QUDT, and the example domains; configurations import
freshly generated bases from that staged tree. Only a successful complete build
is published. `artifacts.py` records file ownership and cleans stale generated
files without touching nested packages or handwritten files. `make regen-check`
checks output bytes and owned file sets in CI.

Extensions include canonical dependency classes in their registry. Imported-class
SHACL restrictions are model-scoped validation profiles, recorded separately from
the canonical class's Python projection. Hydration keeps the selected schemas
even when no local extension instance is present, resolves class-valued links
against the selected symbols, and preserves transitive profiles in snapshots.
WaTr reuses unchanged S223 imports and generates nominal typed views for added
properties, profile ancestry, and authoring policy. `meta.canonical` identifies
the defining dependency class. The compiler linker and export format 3 keep
new identities separate from these projections; shared enums retain identity.
The [identity/profile decision](shared-identities-and-profiles.md) records the
implementation, shape-bundle coverage, and selection rules.

The [hardening plan](compiler-hardening-plan.md) tracks the remaining semantic
upgrade reports and ontology-evolution workflow.

`tests/toy.py` is a hand-written module in exactly the emitter's shape; the
core test suite runs against it so runtime and compiler stay independently
testable. `tests/test_gen.py` compiles `tests/fixtures/mini.ttl` and asserts
behavior (including that emitted code passes `ty check` and that generation
is deterministic).

## The 223 layer

- **`domain223.py`** — the internal capability shared by S223 and WaTr
  registries. It owns named-point authoring/restoration, system and boundary
  interpretation, endpoint ownership, and selection of native planning only
  when there are deferred intentions. Registry inclusion inherits this capability
  without changing imported classes; callers never select a backend.
- **`topology223.py`** — interprets S223 predicates and semantic point ancestry
  for breadth-first walks. Concrete loaded graphs can be walked without Z3.

- **`core/enums.py`** — `EnumValue` constants for punned enumeration
  hierarchies, with `is_a()` walking the parent chain; generated packages
  ship them in an `enums` submodule and register them with the Registry.
- **`connect223.py`** — the connection front end (`S223Connector`),
  installed on the generated `Connectable` root by overlay code. It has two
  jobs: `on_create` materializes shape-required connection points the moment
  equipment is constructed when a slot has one fixed medium, and `connect`
  records a deferred intention.
- **`solver223.py`** — partitions intentions by shared endpoints, encodes
  shape alternatives, cardinality, class, and permitted-media constraints in
  Z3, then ranks valid assignments by domain overlap. It checks uniqueness,
  asks core to cache unchanged component plans, and populates derived objects
  in a core-owned snapshot build. Its interface is a report and an `apply`
  operation. Unsatisfiable cores refer back to authored handles and
  entities.
- **Compiler additions** — metaclass-aware class collection (223 types
  classes with `s223:Class`/`s223:AbstractClass`), `s223:inverseOf`
  handling, the punned enum-subtree carve-out, scalar `hasValue` recognition,
  CP-slot extraction, and the
  medium-domain extraction, and the mutually-required-cycle demotion
  documented in [How connections are resolved](book/explanation/connection-resolution.md).

## Domain configurations and property schemas

`gen/configurations.py` compiles RDF extensions linked through versioned compiler
symbols. It never executes the base package to discover its schema. SHACL supplies
required members, replaceable defaults, finite choices,
named ports, and quantity semantics. Generated constructors and frozen
`PropertySchema` dataclasses expose those requirements to Python tooling.
The exact source graph ships with each package for validation and hydration.
`gen/constraints.py` owns effective property refinement for both front ends;
`gen/symbols.py` owns dependency lookup, format checking, digest verification,
and semantic symbol decoding. Python imports happen normally in the generated
runtime package. Registry inclusion is one runtime operation and does not mutate
the dependency's classes.

`core/points.py` supplies descriptors and references for shape-defined ports.
`core/shape_constraints.py` enforces constructive values on equipment.
`core/property_schema.py` validates quantities and atomically creates independent
properties on equipment, points, or connections. `QuantityAmount` carries an
explicit unit; compiled QUDT dimension metadata checks compatibility without
implicit conversion. Capability and interpretation are independent.

Both `apply_properties(...)` and scalar `quantity(...)` share quantity creation.
`Model.system(...)` collects equipment and junction members and records explicit
boundary points. Connection names do not change port selection; `ports="new"`
requests fresh allocation while preserving shape limits.

## Later phases

- BuildingMOTIF templates as generated subclasses; `as_template()` export;
- blank-node hydration and refresh after direct rdflib mutations.
