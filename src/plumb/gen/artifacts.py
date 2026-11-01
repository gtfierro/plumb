"""Own generated files without touching handwritten files or nested packages."""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST = "_generated.json"


def write_modules(modules: dict[str, str], out: Path) -> None:
    """Write compiler output and remove files owned by the preceding build."""
    # Ownership, not directory contents, determines what can be removed.
    # A parent ontology and its nested configuration packages share a tree;
    # deleting everything absent from this build would erase those children
    # and handwritten helpers. Validate every owned name before the first write.
    files = sorted(modules)
    for filename in files:
        _filename(filename)
    previous = out / MANIFEST
    stale = (
        set(json.loads(previous.read_text())["files"]) if previous.exists() else set()
    )
    for filename in stale - set(files):
        _filename(filename)
    out.mkdir(parents=True, exist_ok=True)
    for filename, source in modules.items():
        (out / filename).write_text(source)
    for filename in stale - set(files):
        (out / filename).unlink(missing_ok=True)
    previous.write_text(json.dumps({"format": 1, "files": files}, indent=2) + "\n")


def _filename(filename: str) -> None:
    if Path(filename).name != filename or filename in {".", "..", MANIFEST}:
        raise ValueError(f"invalid generated filename: {filename!r}")
