# Implementation roadmap

## Next: compiler and runtime hardening

The [compiler hardening plan](compiler-hardening-plan.md) defines the proposed
sequence for making S223/223P and WaTr updates reproducible and predictable:

1. Pin source documents and import closures; gate offline regeneration in CI.
2. Correct constraint composition and establish a shared semantic IR.
3. Extract domain adapters and converge base/configuration compiler semantics.
4. Link imported class identities across S223 and WaTr.
5. Separate core model lifecycle from the S223 resolution backend.
6. Add semantic upgrade reports and ontology-evolution tests.

The plan includes acceptance checks, compatibility constraints, and a prototype
gate for imported classes with package-specific shape restrictions. Import
closure pinning is part of this work, rather than deferred.

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
