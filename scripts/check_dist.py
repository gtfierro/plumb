"""Smoke-test an installed plumb wheel before upload.

``make dist-check`` runs this in a throwaway environment that has only the
built wheel installed, so it catches files missing from the distribution
rather than from the source tree.
"""

from importlib import resources
from pathlib import Path

import plumb
from plumb import Model, connect, s223, watr

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
            "_support.json",
            "_symbols.json",
        ):
            if not (resources.files(f"plumb.{name}") / filename).is_file():
                raise SystemExit(f"plumb.{name} is missing {filename}")

    if watr.Pipe is not s223.Pipe:
        raise SystemExit("unchanged S223 imports lost canonical identity")
    if (
        watr.QuantifiableObservableProperty.meta.canonical
        is not s223.QuantifiableObservableProperty
    ):
        raise SystemExit("WaTr authoring view lost its canonical S223 class")
    if watr.enums.values.Fluid_Water is not s223.enums.values.Fluid_Water:
        raise SystemExit("imported enum values lost canonical identity")
    from plumb.gen.symbols import Symbols

    Symbols.load("plumb.watr")  # Also verify the installed dependency digest.

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
