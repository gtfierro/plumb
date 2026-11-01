# plumb contributor documentation

User documentation, covering how to author, connect, validate, query, and
extend models, is in [the learning book](book/index.md). Build it with
`make docs`; every code cell runs during the build.

The pages here describe how plumb works inside and how to change it:

- [Architecture](architecture.md): the runtime core, the compiler, the 223
  layer, and domain configurations.
- [Code generation](codegen.md): solver translation boundary, inheritance
  repair, UX overlays, and regenerating the committed packages.
- [Traversal API](traversal.md): find, containment navigation, and topology
  walks over loaded and resolved models.
- [Implementation roadmap](roadmap.md): what is done, deferred, and next.
- [Shared identities and profiles](shared-identities-and-profiles.md): the
  canonical S223 imports, typed WaTr views, and model-scoped restrictions.
- [DESIGN.md](../DESIGN.md): the full design rationale.
- [Book sources](book/README.md): how the learning book is laid out and built.

## Status

Phases 1–2 (see DESIGN.md §13): core runtime + compiler + generated Brick
1.4, 223P, and WaTr packages, including enum namespaces, deferred connection
compilation, and a mutable typed object view over existing RDF graphs.
BuildingMOTIF templates and broader round-trip coverage are subsequent phases.

## Development

```bash
uv sync            # install
uv run pytest      # tests
uv run ruff check src tests examples
uv run ty check src tests examples
make docs-check    # build the book; warnings are errors
```

See [CONTRIBUTING.md](../CONTRIBUTING.md) for pull requests and the release
procedure, and `AGENTS.md` for repository conventions.
