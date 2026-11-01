---
file_format: mystnb
kernelspec:
  name: python3
---

# Find classes and values

Ontology classes are Python classes. Enumeration values, such as media and
roles, are `EnumValue` objects in the package's `enums` module. Both can be
browsed as trees.

## Browse a class branch

```{code-cell} python3
from plumb.watr import Process

print(Process.meta.tree(max_depth=2))
```

| Attribute | Gives |
| --- | --- |
| `meta.children` | direct subclasses |
| `meta.descendants` | all subclasses |
| `meta.parents` | direct parents |
| `meta.tree(max_depth=...)` | printable subtree |

A class with several parents appears under each one.

## Select a class

Look up a class within a branch by short name, Python name, or IRI:

```{code-cell} python3
from plumb.watr import Process_ReverseOsmosis

selected = Process.meta["ReverseOsmosis"]
selected is Process_ReverseOsmosis, selected.meta.iri
```

The lookup raises `KeyError` outside the branch. `issubclass()` and
`isinstance()` work as usual.

## Inspect a class

`.meta` gives a class's ontology provenance:

```{code-cell} python3
from plumb.watr import SedimentationTank

SedimentationTank.meta.iri, SedimentationTank.meta.label, SedimentationTank.meta.parents
```

```{code-cell} python3
print(SedimentationTank.meta.definition)
```

`meta.properties` lists the generated attributes and `describe_ports()` the
connection points. On an object, `meta.instance_iri` and `meta.model`
identify it.

## List every class

Each package's `REGISTRY` lists its classes:

```{code-cell} python3
from plumb import watr

len(watr.REGISTRY.classes), watr.REGISTRY.resolve("Process_ReverseOsmosis")
```

The [class catalog](../reference/catalog.md) lists every S223 and WaTr class.

## Browse enumeration values

`enums.values` holds every value under a flat name. The top level of `enums`
holds the branches, for tab completion:

```{code-cell} python3
from plumb.watr import enums

water = enums.Substance.Medium.Mix.Fluid.Water
water is enums.values.Fluid_Water
```

```{code-cell} python3
water.tree(max_depth=2)
```

Values have `children`, `descendants`, `parent`, and `parents`, without a
`.meta` step. `tree_text()` returns the tree as a string.
Shared values are the canonical S223 objects. Tree browsing shows the defining
package's children; WaTr additions are available in `enums.values` and retain
their ancestry without changing S223's enum trees.

## Select a value

Bracket lookup searches a subtree by short name, flat name, or IRI:

```{code-cell} python3
chilled = enums.values.Water_ChilledWater
water["ChilledWater"] is chilled, water[chilled.iri] is chilled
```

An ambiguous short name raises `KeyError` listing the matches.

## Check ancestry

`is_a()` follows every parent:

```{code-cell} python3
sludge = enums.values.Fluid_Sludge
sludge.is_a(enums.values.Mix_Fluid), sludge.is_a(enums.values.Fluid_Water)
```

Sludge is a fluid mixture, not a kind of water.
