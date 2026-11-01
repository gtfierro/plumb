"""Compile packages with ``plumb gen`` and review upgrades with ``plumb diff``.

Compile an ontology into a generated Python package:

    # from a local file (no network)
    plumb gen --file Brick.ttl --name Brick --out src/plumb/brick

    # by IRI, resolving the owl:imports closure through ontoenv
    plumb gen --iri https://brickschema.org/schema/1.4/Brick \\
                  --name Brick --out src/plumb/brick
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import rdflib

from .gen import generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="plumb")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("gen", help="generate a Python package from an ontology")
    src = gen.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", "-f", type=Path, help="local ontology file")
    src.add_argument("--iri", "-i", help="ontology IRI (resolved via ontoenv)")
    gen.add_argument(
        "--name", "-n", required=True, help="ontology short name, e.g. Brick"
    )
    gen.add_argument(
        "--out", "-o", type=Path, required=True, help="output package directory"
    )
    gen.add_argument(
        "--extra",
        type=Path,
        action="append",
        default=[],
        help="additional graphs to merge (e.g. separate shapes files)",
    )
    gen.add_argument(
        "--source",
        help="canonical source identity recorded in package metadata; "
        "defaults to --file/--iri",
    )
    gen.add_argument(
        "--no-overlay",
        action="store_true",
        help="skip built-in UX overlay registrations",
    )

    diff = sub.add_parser("diff", help="review changes between generated packages")
    diff.add_argument("before", type=Path, help="saved baseline package directory")
    diff.add_argument("after", type=Path, help="candidate package directory")
    diff.add_argument("--json", action="store_true", help="emit a structured report")

    args = parser.parse_args(argv)
    if args.command == "diff":
        from .gen.review import compare_packages

        try:
            report = compare_packages(args.before, args.after)
        except ValueError as error:
            diff.error(str(error))
        print(report.to_json() if args.json else report.render(), end="")
        return 0
    if args.command == "gen":
        try:
            return _cmd_gen(args)
        except ValueError as error:
            gen.error(str(error))
    return 2  # pragma: no cover - argparse enforces the subcommand


def _cmd_gen(args: argparse.Namespace) -> int:
    graph = rdflib.Graph()
    if args.file is not None:
        graph.parse(args.file)
        source: str | None = str(args.file)
    else:
        graph, source = _load_via_ontoenv(args.iri)
    for extra in args.extra:
        graph.parse(extra)

    target = generate(
        graph,
        args.out,
        name=args.name,
        source=args.source or source,
        overlay=None if args.no_overlay else "auto",
    )
    print(f"wrote {target} ({len(graph)} triples in)", file=sys.stderr)
    return 0


def _load_via_ontoenv(iri: str) -> tuple[rdflib.Graph, str]:
    """Fetch an ontology and its owl:imports closure through ontoenv.

    Uses a temporary environment, so the closure reflects the network state
    at generation time. Committed packages instead use the locked offline
    workflow in scripts/regenerate.py.
    """
    from ontoenv import OntoEnv

    env = OntoEnv(temporary=True)
    env.add(iri)
    graph, _closure = env.get_closure(iri)
    env.close()
    return graph, iri


if __name__ == "__main__":
    raise SystemExit(main())
