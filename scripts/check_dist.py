"""Smoke-test an installed plumb wheel before upload.

``make dist-check`` runs this in a throwaway environment that has only the
built wheel installed, so it catches files missing from the distribution
rather than from the source tree.
"""

from importlib import resources
from pathlib import Path

import plumb
from plumb import Model, connect, watr

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = (
    "brick",
    "s223",
    "s223.hvac",
    "watr",
    "watr.asm2d",
    "watr.drinking_water",
    "watr.seawater_ro",
)


def main() -> None:
    installed = Path(plumb.__file__).resolve()
    if installed.is_relative_to(ROOT / "src"):
        raise SystemExit(f"imported the source tree, not the wheel: {installed}")

    for name in PACKAGES:
        shapes = resources.files(f"plumb.{name}") / "_shapes.ttl"
        if not shapes.is_file():
            raise SystemExit(f"plumb.{name} is missing _shapes.ttl")
    if not (resources.files("plumb") / "py.typed").is_file():
        raise SystemExit("plumb is missing py.typed")
    for name in ("s223", "watr"):
        for filename in (
            "_build.json",
            "_generated.json",
            "_connection_support.json",
            "_symbols.json",
        ):
            if not (resources.files(f"plumb.{name}") / filename).is_file():
                raise SystemExit(f"plumb.{name} is missing {filename}")

    with Model("urn:example/dist-check#") as model:
        clarifier = watr.Clarifier("clarifier")
        connect(watr.Chiller("source"), watr.Pump("pump"))
        connect(model["pump"], watr.Tank("tank"))
    if watr.Process_Settling not in clarifier.has_process:
        raise SystemExit("class defaults were not applied")
    model.resolve()
    model.validate()

    print(f"plumb {plumb.__version__} wheel OK ({installed.parent})")


if __name__ == "__main__":
    main()
