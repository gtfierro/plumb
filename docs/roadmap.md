# Implementation roadmap

## Next: compiler and runtime hardening

The [compiler hardening plan](compiler-hardening-plan.md) defines the active
sequence for making S223/223P and WaTr updates reproducible and predictable:

1. Pin source documents and import closures; gate offline regeneration in CI.
2. Correct constraint composition and establish a shared semantic IR.
3. Extract domain adapters and converge base/configuration compiler semantics.
4. Link imported class identities across S223 and WaTr.
5. Separate core model lifecycle from the S223 resolution backend.
6. Add semantic upgrade reports and ontology-evolution tests.

The plan includes acceptance checks and a prototype gate for imported classes
with package-specific shape restrictions. Breaking changes are authorized;
the target interfaces take priority over compatibility wrappers. Import
closure pinning is part of this work, rather than deferred.

Implemented so far: verified offline input snapshots and regeneration CI;
effective property intersections and numeric counts; RDF ancestry independent
of Python MRO; predicate name disambiguation; atomic collection updates; and
an initial S223 semantic adapter using vocabulary IRIs and subclass ancestry.
Both compiler fronts now share property refinement and rendering, including
required/default values and finite choices. Extensions link through versioned,
hashed compiler symbol exports rather than private runtime registries. Required
and optional policy bindings have structured diagnostics, and every generated
package carries a source-linked enforcement report.
The [identity/profile implementation](shared-identities-and-profiles.md) links
the committed WaTr package to canonical S223 classes and enum values, with
explicit nominal views for added properties, ancestry, and authoring policy.
Transitive profiles, mixed hydration, connections, containment, class-valued
terms, and static typing are covered in both package/registry orders.

Design criterion: deep modules with simple interfaces. These phases assign
ownership of complexity; they should reduce caller coordination and keep
compiler passes, adapters, and backend selection behind small public APIs.

## Completed in the current framework pass

- Strict `Model.compile(validate=True)` with local, reproducible shape bundles.
- Multiple-inheritance constructor unioning; punned terms remain reference
  instances rather than generated instantiable classes.
- Named ports, solver-level paired-port medium propagation, and concrete
  `pairedConnectionPoint` materialization.
- System member scopes and solver-derived boundary connection points.
- QUDT 3.4.0 unit and quantity-kind vocabularies compiled through ontoenv,
  QUDT quantity values, and concise quantity authoring.
- A nominal stream-state authoring view using existing S223/WaTr semantics.
- Per-connection solver explanations with authored and inferred evidence.
- BeautifulSoup-style traversal: narrowing filters with `exact()`,
  containment search, and topology walks with `through=` path filters
  ([traversal.md](traversal.md)).

## Deferred deliberately

- Logical/property-package translation. Revisit after the ontology-facing
  quantity and stream-state patterns settle.
- Source traceability/provenance for generated model facts. Revisit before
  adding interchange or translation workflows.

## Later development line

A translator between S223/WaTr and WaterTAP is on the development timeline.
WaterTAP itself is not modeled by this framework today. Translation needs an
explicit mapping ontology or mapping package for unit models, ports, state
variables, assumptions, and provenance; free-text comments are not a semantic
translation contract.
