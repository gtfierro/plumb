# Model lifecycle

```text
generated classes → authored model → check() → resolve() → graph() / save()
                                                         └→ validate() / compile()
```

## Generate

The compiler turns an ontology and its SHACL shapes into a Python package
ahead of time. Model scripts import the package; they never run the compiler.

## Author

An authored `Model` is mutable. Constructors check required properties,
attributes check their values, and inverse relations stay in sync.
`connect()` records an intention and returns a handle. Points the shapes fix
are created with the equipment; the rest wait for resolution.

## Resolve

`check()` checks deferred intentions without changing authored objects. S223
and WaTr intentions use the shared Z3 planner; ordinary RDF models need no
connection planning. `resolve()` produces a frozen `ResolvedModel` with every
connection point, connection, and inverse relation. The authored model is not
changed, and any later edit invalidates the snapshot. See
[How connections are resolved](connection-resolution.md).

Core owns copying, transactions, caching, and freezing. Domain selection is
automatic; model authors keep using `Model.check()` and `Model.resolve()`.

`find_all()` works on any model, but walks such as `find_all_next()` follow
concrete pipes and points. An authored model gets those only from
resolution, so walk the snapshot (`model.resolve()["pump"].find_all_next()`);
walking an authored model with unresolved connections raises
`ModelingError`.

## Validate

`validate()` runs shifty on the resolved RDF: SHACL-AF rules, then SHACL Core
validation, against the shapes bundled with each package. `compile()`
resolves and validates in one call. `graph()` and `save()` resolve but do not
validate.

## Load

`Model.from_graph()` builds objects from existing RDF. A loaded model is
backed by its graph, and edits write through to it. Its connections are already
concrete: `resolve()` copies and freezes them without invoking the planner,
preserving original IRIs, unprojected RDF, and the loaded point projection.
Deferred `connect()` and `model.system()` are unavailable, but its pipes and
points are concrete, so it can be searched and walked directly. See
[Save, load, and edit models](../how-to/save-and-load.md).

The internals are in `docs/architecture.md` in the repository.
