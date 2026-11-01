"""Verified, offline compiler inputs. Import resolution belongs to source updates.

The lock records documents or explicitly labelled closure snapshots. Loading never
follows ``owl:imports``: those dependencies must already be captured in the lock.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from rdflib import Graph


class SourceLock:
    """Load a named input graph after verifying every locked source's bytes."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._data: dict[str, Any] = json.loads(self.path.read_text())
        if self._data.get("format") != 1:
            raise ValueError(f"{self.path}: unsupported source lock format")

    def load(self, name: str) -> Graph:
        """Return a fresh graph; missing, corrupt, or unknown inputs fail closed."""
        try:
            inputs = self._data["graphs"][name]
        except KeyError:
            raise ValueError(f"{self.path}: unknown input graph {name!r}") from None
        graph = Graph()
        for key in inputs:
            source = self._data["sources"][key]
            path = self.path.parent / source["path"]
            try:
                data = path.read_bytes()
            except FileNotFoundError:
                raise ValueError(f"{name}: missing source {key}: {path}") from None
            actual = hashlib.sha256(data).hexdigest()
            # Verify raw bytes before parsing. A graph-equivalent rewrite is
            # still a different captured input and needs an explicit lock
            # update; ordinary generation must never bless changed sources or
            # resolve a missing owl:imports dependency from the network.
            if actual != source["sha256"]:
                raise ValueError(
                    f"{name}: SHA-256 mismatch for {key} ({path}): "
                    f"expected {source['sha256']}, got {actual}"
                )
            # Explicit format and base avoid RDF format detection or external loads.
            graph.parse(data=data, format="turtle", publicID=source["identity"])
        return graph

    def provenance(self, name: str) -> dict[str, Any]:
        """Return the exact source records to include in build metadata."""
        return {key: self._data["sources"][key] for key in self._data["graphs"][name]}
