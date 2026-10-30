"""Regenerate all supported packages offline, or check them with --check.

Build in an isolated source tree so configurations link against freshly built
bases. Only publish output after the entire build succeeds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from plumb.gen import compile_modules
from plumb.gen.artifacts import MANIFEST, write_modules
from plumb.gen.sources import SourceLock
from plumb.gen.vocabulary import emit_vocabulary_module

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "s223": ("S223", "https://open223.info/223p.ttl", "s223"),
    "watr": ("WATR", "ontology/watr-0.3.0rc1.ttl", "watr"),
    "asm2d": ("ASM2d", "ontology/asm2d.ttl", "watr/asm2d"),
    "seawater-ro": ("SeawaterRO", "ontology/seawater-ro.ttl", "watr/seawater_ro"),
    "drinking-water": (
        "DrinkingWater",
        "ontology/drinking-water.ttl",
        "watr/drinking_water",
    ),
    "hvac": ("HVAC", "ontology/hvac.ttl", "s223/hvac"),
}


def build(destination: Path) -> None:
    lock = SourceLock(ROOT / "ontology/sources.lock.json")
    for key, (name, source, package) in PACKAGES.items():
        print(f"Compiling {name}", flush=True)
        modules = compile_modules(lock.load(key), name=name, source=source)
        modules["_build.json"] = _provenance(lock, key)
        write_modules(modules, destination / package)
    graph = lock.load("qudt")
    modules = {}
    for filename, name, rdf_type, namespace in (
        ("units.py", "QUDT units", "Unit", "unit"),
        ("quantity_kinds.py", "QUDT quantity kinds", "QuantityKind", "quantitykind"),
    ):
        modules[filename] = emit_vocabulary_module(
            graph,
            name=name,
            rdf_types=(f"http://qudt.org/schema/qudt/{rdf_type}",),
            primary_namespace=f"http://qudt.org/vocab/{namespace}/",
            ontology_iri="http://qudt.org/3.4.0/qudt-all",
        )
    modules["_build.json"] = _provenance(lock, "qudt")
    write_modules(modules, destination / "qudt")


def _provenance(lock: SourceLock, key: str) -> str:
    compiler = hashlib.sha256()
    for path in sorted((ROOT / "src/plumb/gen").glob("*.py")):
        compiler.update(path.name.encode() + b"\0" + path.read_bytes())
    return (
        json.dumps(
            {
                "format": 1,
                "compiler": {"name": "plumb", "sha256": compiler.hexdigest()},
                "sources": lock.provenance(key),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail on generated drift")
    parser.add_argument("--output", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.output is not None:
        build(args.output)
        return
    with TemporaryDirectory(prefix="plumb-regen-") as temporary:
        stage = Path(temporary) / "src/plumb"
        shutil.copytree(
            ROOT / "src/plumb", stage, ignore=shutil.ignore_patterns("__pycache__")
        )
        env = {**os.environ, "PYTHONPATH": str(stage.parent)}
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--output", str(stage)],
            env=env,
            check=True,
        )
        differences = []
        for package in [value[2] for value in PACKAGES.values()] + ["qudt"]:
            built = stage / package
            target = ROOT / "src/plumb" / package
            files = json.loads((built / MANIFEST).read_text())["files"]
            modules = {filename: (built / filename).read_text() for filename in files}
            if args.check:
                previous = target / MANIFEST
                old_files = (
                    json.loads(previous.read_text())["files"]
                    if previous.exists()
                    else []
                )
                for filename in sorted(set(files) | set(old_files) | {MANIFEST}):
                    actual, expected = target / filename, built / filename
                    if (
                        not actual.exists()
                        or not expected.exists()
                        or actual.read_bytes() != expected.read_bytes()
                    ):
                        differences.append(f"{package}/{filename}")
            else:
                write_modules(modules, target)
        if differences:
            raise SystemExit("Generated output differs:\n" + "\n".join(differences))
        print(
            "Generated packages are current."
            if args.check
            else "Generated packages updated."
        )


if __name__ == "__main__":
    main()
