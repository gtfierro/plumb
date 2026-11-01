"""Compare connection planning and snapshot costs with deterministic RDF hashes.

Run with: uv run python scripts/benchmark_resolution.py --repeats 3
Construction and graph serialization are outside the timed check/resolve pair.
"""

import argparse
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location
import hashlib
import json
from statistics import median
from time import perf_counter
from plumb import Model, connect, s223, watr

ROOT = Path(__file__).resolve().parents[1]


def air() -> Model:
    with Model("urn:bench:air#") as model:
        for i in range(30):
            connect(s223.Damper(f"d{i}"), s223.Fan(f"f{i}"))
    return model


def water() -> Model:
    with Model("urn:bench:water#") as model:
        nodes = [watr.Tank(f"t{i}") for i in range(20)]
        for a, b in zip(nodes, nodes[1:]):
            connect(a, b, medium=watr.enums.values.Fluid_Water)
    return model


def ro() -> Model:
    path = ROOT / "examples/watr/seawater_ro/watertap_seawater_ro_full.py"
    spec = spec_from_file_location("bench_ro", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark example {path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_model()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    results = {}
    for name, build in [("air", air), ("water", water), ("ro", ro)]:
        timings = []
        for _ in range(args.repeats):
            model = build()
            start = perf_counter()
            report = model.check()
            if not report.complete:
                raise RuntimeError(f"{name}: benchmark is not resolvable: {report}")
            snapshot = model.resolve()
            timings.append(perf_counter() - start)
        graph = snapshot.graph()
        digest = hashlib.sha256(
            "\n".join(sorted(graph.serialize(format="nt").splitlines())).encode()
        ).hexdigest()
        results[name] = {
            "seconds": median(timings),
            "entities": len(snapshot),
            "sha256": digest,
        }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
