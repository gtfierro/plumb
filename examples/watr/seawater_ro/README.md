# Seawater reverse osmosis

Run from the repository root:

```bash
uv run python examples/watr/seawater_ro/watertap_seawater_ro_full.py
```

The script writes `seawater_ro_full.ttl` and describes the concrete routing of
27 connections, including the pressure exchanger's two paired circuits.

Equipment configurations and quantity schemas are imported from
`plumb.watr.seawater_ro`. Their processes, roles, named branch ports,
quantity kinds, units, labels, and nominal aspects come from
[ontology/seawater-ro.ttl](../../../ontology/seawater-ro.ttl). For example:

```python
feed.outlet.apply_properties(
    SeawaterFeedState(
        flow_rate=Q(7.05e6, units.GAL_US_PER_DAY),
        total_dissolved_solids=Q(35.0, units.GM_PER_L),
        total_suspended_solids=Q(0.03, units.GM_PER_L),
        temperature=Q(298.0, units.K),
        pressure=Q(100000.0, units.PA),
    ),
    prefix="influent",
)
```

`MembraneDesign`, `HighPressurePumpDesign`, `PumpDesign`, `ResidenceTimeDesign`,
`PressureExchangerDesign`, `PermeateState`, and `UVDesign` use the same
`apply_properties(...)` API. Bare numbers use source-declared default units;
`Q` is the library's `QuantityAmount` imported under a short name. Each
application creates
separate RDF properties, so a storage design can be reused safely.

The full model uses broad water media to permit composition changes along the
train; salt and suspended-solids concentrations carry substance qualifications.
The [standalone pretreatment example](../seawater_ro_pretreatment/) preserves
its seawater inlet and lets the resolver propagate that more specific medium.

`model.system(...)` collects all 26 equipment and junction members. The treated
backwash and landfill outlets are explicitly marked as boundary points. Feed,
brine disposal, and municipal supply remain equipment nodes as in the original
reference model. Property-package interfaces remain semantic boundary nodes.
The permeate pressure stays on the permeate connection.

Water permeability remains an ordinary scalar `Property`: the bundled vocabulary
has no compatible quantity kind for its coefficient. Its label preserves the
unit. The example describes nominal design values and topology; it does not
solve the WaterTAP process equations.

Regenerate the domain packages with:

```bash
make regen
```
