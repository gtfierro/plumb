# SHACL-defined cooling coil

Run `uv run python examples/s223/cooling_coil/cooling_coil.py` from the repository
root. It writes an instance graph and its portable ontology schema.

The model imports `AirWaterCoolingCoil` from `plumb.s223.hvac`. Its four
named points (`air_inlet`, `air_outlet`, `water_inlet`, and `water_outlet`) and
fixed media are defined in [ontology/hvac.ttl](../../../ontology/hvac.ttl).
The same configuration is used by the [AHU example](../ahu/).

Edit the RDF/SHACL source and run
`make regen` to regenerate the API.
Model authors need no handwritten subclasses, policy dictionaries, or point
declarations.
