# Changelog

All notable changes to plumb are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html). While
the version is below 1.0, minor releases may change the public API.

## [Unreleased]

## [0.2.0] - 2026-11-01

### Added

- Locked, verified ontology snapshots and offline regeneration for S223, WaTr,
  QUDT, and domain configurations. Generated packages record their source inputs,
  exported symbols, and constraint support for review.
- `plumb diff BEFORE AFTER` compares saved compiler packages without importing
  them. Text and JSON reports distinguish contract changes from source provenance
  changes. See [the ontology upgrade guide](docs/ontology-upgrades.md).
- Structured compiler diagnostics for missing adapter bindings, incompatible
  dependencies, and unsupported projections.

### Changed

- Ontologies and domain configurations now compile through a shared intermediate
  representation. Property constraints compose before rendering, and ontology
  ancestry is preserved independently of Python inheritance.
- WaTr reuses canonical S223 classes and enumeration values. Water-specific
  constructors and properties live in typed views; selected validation profiles
  remain scoped to the model and survive RDF hydration and snapshots. Import
  canonical classes from `plumb.s223` and water authoring classes from
  `plumb.watr`; see [shared identities and profiles](docs/shared-identities-and-profiles.md).
- Optional collection arguments in generated constructors use `None` to request
  defaults. An explicit empty collection now overrides those defaults.
- The runtime owns transactions, immutable snapshots, and bounded resolution
  caches. S223 connection rules sit behind a domain interface; plain RDF models
  do not load the connection planner.
- Generated packages use symbol manifest format 3 and support report format 2.
  Regenerate custom packages with this compiler before using them as dependencies.

### Fixed

- Conjunctive property ranges, count refinements, enum defaults, and inverse
  relation updates now preserve their combined constraints.
- Connection-point selection follows semantic direction rather than Python class
  names or inheritance. Resolution explanations share the planner's medium rules.
- Failed construction restores model state, and cached plans and snapshots retain
  consistent labels, pairings, provenance, and validation profiles.

## [0.1.0] - 2026-10-21

First public release.

### Added

- Typed Python packages generated from ontologies and their SHACL shapes:
  Brick 1.4.2, ASHRAE 223P (v1.0.0-2026), WATR v0.3.0.rc1, and QUDT units and
  quantity kinds. Generated classes carry ontology definitions and typed
  constructors, so editors and type checkers see the whole vocabulary.
- `Model` sessions that serialize authored objects to Turtle, with containment
  through `with` blocks, flow connections through `>>` and `connect()`, and
  SHACL validation through shifty whose reports name the authored objects.
- Deferred 223P and WATR connections: the Z3 resolver chooses connection
  points, media, and Connection classes, and `explain()` reports why.
- `Model.from_graph()` to load existing RDF as typed, editable objects, with
  optional SHACL-AF inference, plus querying helpers. Packages, including the
  bundled domain configurations, are selected from the graph's `owl:imports`.
- Domain configurations and immutable property schemas compiled from SHACL,
  with QUDT-aware quantities (`apply_properties()`, `quantity()`).
- `.sensor()` on equipment, points, ports, and connections creates an observed
  property and the most specific sensor class for its quantity kind.
  `.actuator()` on equipment creates a command property and an `Actuator`.
  Both accept a QUDT quantity kind or an enumeration kind such as
  `Binary_OnOff`.
- A sensor's observation or reference location may be a deferred connection,
  port, or declared point; resolution places it on the concrete entity.
- Property schemas written in Python: subclass `PropertySchema` and declare
  fields with `quantity_field()`.
- `flowsheet(model)` draws a resolved S223 or WATR model as a flow sheet
  through Graphviz: streams coloured by medium, unit operations listing their
  processes and objectives, instrument bubbles, system clusters, and
  boundary terminals.
- WATR process and treatment-objective defaults implied by an equipment
  class's shapes are filled in at construction.
- The `plumb gen` command for compiling other ontologies, with
  deterministic output for an unchanged imports closure.
- BeautifulSoup-style traversal: `find()`/`find_all()` with class, attribute,
  and `exact()` filters on models and objects; containment navigation
  (`contents`, `container`, `find_parent()`); and flow walks
  (`find_all_next()`, `find_all_previous()`, `walk()`) with `through=` and
  `descend=`.
- `maps_to` on ports and named points, so a part's point can map onto a
  container port that exists only after resolution. The resolver gives both
  points one medium and direction.

### Changed

- Compared with pre-release builds, multi-valued enum properties such as
  `has_role` and equipment `medium` return a live collection with `add()`,
  `remove()`, and `clear()` instead of a plain `list`. Each change is
  range-checked and shape-checked. Code that called `.append()` on the old list must use
  `.add()`; comparisons with lists, such as `duct.has_role == [...]`, still
  work.
- Equipment whose shapes require connection points in only one direction,
  such as WaTr's separation tanks and 223P's electrical appliances, now
  accepts deferred connections in the other direction instead of reporting
  them as unsatisfiable. `UnsatisfiableModelError` messages name the
  conflicting constraints.
- Deferred connections resolve for equipment whose shapes need several points
  of one class (an `IceMaker`'s electricity and water inlets), forbid a class
  outright (`AirHeatExchanger`), or require identical points
  (`DualDuctTerminal`'s two air inlets). Points created from shapes are named
  after their owner, such as `hx-in-2`, rather than `inlet_connection_point_1`.
- A port or connection point with an explicit medium is no longer held to the
  media its class's shapes mention, so a `Fan` can have a declared
  electricity inlet. Medium-domain conflicts now appear in unsatisfiable cores.

[Unreleased]: https://github.com/gtfierro/plumb/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/gtfierro/plumb/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/gtfierro/plumb/releases/tag/v0.1.0
