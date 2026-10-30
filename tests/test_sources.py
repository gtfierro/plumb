"""Locked inputs and file ownership fail safely at the compiler boundary."""

import hashlib
import json

import pytest

from plumb.gen.sources import SourceLock


def test_locked_sources_verify_bytes_and_do_not_fetch_imports(tmp_path):
    data = (
        b"<urn:x> <http://www.w3.org/2002/07/owl#imports> <https://invalid.invalid/> ."
    )
    source = tmp_path / "source.ttl"
    source.write_bytes(data)
    path = tmp_path / "sources.lock.json"
    path.write_text(
        json.dumps(
            {
                "format": 1,
                "sources": {
                    "x": {
                        "path": "source.ttl",
                        "identity": "urn:x",
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                },
                "graphs": {"example": ["x"]},
            }
        )
    )
    lock = SourceLock(path)
    assert len(lock.load("example")) == 1
    source.write_bytes(data + b"\n")
    with pytest.raises(ValueError, match="example: SHA-256 mismatch for x"):
        lock.load("example")
    source.unlink()
    with pytest.raises(ValueError, match="example: missing source x"):
        lock.load("example")
