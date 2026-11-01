# Reviewing an ontology upgrade

An ordinary supported update changes locked source documents and regenerated
output. Compiler or runtime edits are needed only when a new construct falls
outside the supported projection, or when authoring policy intentionally changes.

## Capture the baseline

Use the same compiler for both source versions. This isolates ontology changes
from compiler changes and ensures both sides export current metadata formats.
Start with unchanged locked inputs and current generated packages:

```bash
make regen-check
PLUMB_REVIEW_DIR=$(mktemp -d)
cp -R src/plumb/s223 "$PLUMB_REVIEW_DIR/s223"
cp -R src/plumb/watr "$PLUMB_REVIEW_DIR/watr"
```

The copies include nested configuration packages. If the baseline predates the
review metadata, regenerate its old locked inputs with the current compiler
before saving it. Keep compiler changes in separate commits from ontology updates
where possible.

## Update the source lock

Acquire and review the intended upstream documents explicitly. Ordinary
generation never retrieves sources or resolves new network imports. Record
each document's identity, version, import relationships, local path, and SHA-256
in `ontology/sources.lock.json`. Preserve the distinction between original
documents, local additions, and historical closure snapshots; do not relabel a
closure as a verified upstream document.

S223 and WaTr must use a compatible shared S223/QUDT closure. Update every
affected graph entry and its dependencies together. See
[snapshot provenance](../ontology/snapshots/README.md) for the captured baseline.
Source hashes are byte identities; a hash change alone says nothing about
behavioral compatibility.

## Regenerate and review

```bash
make regen
uv run plumb diff "$PLUMB_REVIEW_DIR/s223" src/plumb/s223
uv run plumb diff "$PLUMB_REVIEW_DIR/watr" src/plumb/watr --json > watr-upgrade.json
uv run plumb diff "$PLUMB_REVIEW_DIR/s223/hvac" src/plumb/s223/hvac
uv run plumb diff "$PLUMB_REVIEW_DIR/watr/asm2d" src/plumb/watr/asm2d
uv run plumb diff "$PLUMB_REVIEW_DIR/watr/seawater_ro" src/plumb/watr/seawater_ro
uv run plumb diff "$PLUMB_REVIEW_DIR/watr/drinking_water" src/plumb/watr/drinking_water
git diff --stat
```

Regeneration stages all packages and links configurations against freshly built
bases before publishing output. Generated file ownership removes stale output
while preserving nested packages and handwritten files. Never patch generated
classes to accommodate an update.

`plumb diff` reads saved `_symbols.json`, `_support.json`, and optional
`_build.json` files. It executes no package code and needs no installed historical
dependencies. The report has two sections:

| Section | Compared facts |
| --- | --- |
| Contract changes | Classes, enum members, named terms, semantic ancestry, Python names/bases/views, effective property ranges/counts/defaults/choices, named ports and port expressions, quantity projections, binding requirements/status, and constraint enforcement |
| Provenance changes | Ontology identity/version/source, captured graph bytes, compiler fingerprint, locked documents and versions, and pinned dependency digests |

Changes identify semantic targets and property paths. Anonymous source labels and
explanatory prose do not define contract identity. Anonymous constraint values
have fingerprints of their rooted RDF contents, including query text. Supported
conjunction wrappers and finite-choice ordering do not create contract changes.
Repeated `xone` branches remain significant. An unsupported or validation-only
expression can still change its fingerprint without changing the enforcement
category.

The report is a review aid, not an OWL/SHACL equivalence prover or a compatibility
certification. Equivalent rewrites outside the normalized subset can be reported
as changes. Documentation and RDF outside the projected constraint inventory may
change only provenance; inspect the source and generated diffs whenever source
identity changes. A dependency digest change requires reviewing that dependency
directly: the report does not reconstruct its historical contents from the
current installation. The separate QUDT vocabulary catalog has no class/compiler
export; review its generated constants and locked input diff directly.

The text and JSON forms contain the same facts, sorted deterministically. JSON
report format 1 has `changes` and `provenance_changes`; each change records its
kind, category, target, optional path, field, and before/after values. Differences
return status zero. Missing, invalid, or unsupported metadata returns status two
with an actionable error. Both sides need compiler symbols format 3 and support
report format 2.

Review `_support.json` and the source shapes for changes that remain validation
only. Missing required policy targets identify the binding and fail compilation
before overwriting existing output. Optional targets are reported explicitly.
Unsupported constructive values identify the affected predicate/constraint;
decide whether to extend the shared compiler or change the source authoring
projection. Keep S223 vocabulary interpretation in `gen/s223.py`, policy in
`gen/overlays.py`, and general constraint composition in `gen/constraints.py`.

## Verify and commit

```bash
make check
make regen-check dist-check docs-check
make examples
```

Review example RDF changes as ontology effects, then commit the source/lock,
generated output, and relevant example or documentation updates together.
Add a focused regression when a new source construct requires compiler work.
The semantic report can accompany the pull request alongside those diffs.

`tests/test_ontology_evolution.py` demonstrates the supported maintenance path
using locked, local fixtures. It covers additions, narrowed ranges, changed
cardinalities/defaults, generated positive/negative typing, validation and RDF
round trips, plus changed water-port groups in mixed S223/WaTr models. It checks
graph isomorphism as well as byte-identical generation after fresh parsing and
reversed triple insertion. `tests/test_upgrade_review.py` additionally covers
equivalent shape syntax, name collisions, enum ancestry, support status, query
changes, unavailable historical dependencies, and malformed metadata.
The normal CI test matrix and offline regeneration gate run these checks.
