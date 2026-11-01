# Shared ontology identities and model profiles

Decision: reuse canonical dependency objects and represent added authoring
surfaces with explicit nominal Python views. The committed WaTr package now
links to S223 through compiler symbols; the earlier integration prototype remains
a regression fixture for model-scoped SHACL restrictions.

## Identity and public imports

S223 owns its ontology classes and enumeration values. An unchanged imported
class is the exact S223 Python object, also available through WaTr. When WaTr
adds properties, ancestry, or authoring policy, its compiler emits a typed
subclass of the canonical class with the same RDF IRI. This view owns descriptors
for additions/refinements and inherits unchanged descriptors and connection
constraints from its canonical base.

```python
from plumb import s223, watr

assert watr.Pipe is s223.Pipe
assert issubclass(watr.QuantifiableObservableProperty,
                  s223.QuantifiableObservableProperty)
assert watr.QuantifiableObservableProperty.meta.canonical is s223.QuantifiableObservableProperty
```

Import canonical classes from `plumb.s223` and water authoring classes from
`plumb.watr`. Existing water imports select the water property surface. A view
has its own package metadata but does not declare another ontology class or
modify its canonical base. `meta.iri` identifies the RDF term; `meta.canonical`
identifies its defining Python class; `meta.registry` identifies the selected
projection. Python range annotations use canonical dependency types so ordinary
instances and water views type-check together.

The pinned closures share 181 class IRIs: 54 reuse canonical objects and 127
have explicit views, including the Connectable view that owns WaTr policy.
These counts follow from source constraints and policy, rather than a class
list maintainers must update. Local WaTr terms remain ordinary generated classes.

## Profiles and hydration

SHACL constraints on imported classes apply to the model graph when the water
schema is selected. They do not modify shared constructors, install descriptors
globally, or change S223's registry. Water views additionally expose compiled
authoring constraints in signatures and descriptors. A canonical constructor
may accept a value that a selected profile later rejects; `Model.compile()`
validates the finished graph by default.

The prototype limits quantifiable observable properties to 100 in its water
profile. A shared property with value 120 remains valid in a plain S223 model
and fails in the profile model, including when hydrated as an imported class.
Profile-only constraints are marked `profile: true` and validation-only in the
support report. Canonical constructors do not silently acquire profile defaults;
the configuration compiler rejects those defaults and imported identity changes.

Ordinary authored models select schemas through local classes and views.
Hydration retains explicitly selected registries even if every instance uses an
imported term. Compatible views are selected by nominal subtyping, independently
of registry order; unrelated equal-IRI definitions and incompatible sibling views
fail explicitly. Class-valued links resolve against the selected model symbols,
since a canonical registry cannot know future extension classes. Invalid graphs
remain inspectable until validation.

Transitive local profiles compose by conjunction and survive snapshot creation.
A linked ontology's full closure covers its dependency bundles; validation loads
that closure once rather than duplicating anonymous SHACL expressions. Local
configuration schemas add their own shapes. Large closures are parsed once on
first use. `export_ontology()` exports local configuration schemas without
copying complete dependency closures into each configuration export.

The loader selects installed packages through RDF `owl:imports`. Custom profiles
without a package mapping still supply `registries=` on hydration. Importing a
module alone does not activate its profile in unrelated models.

## Enumeration and authoring policy

All 412 imported enum values are the exact S223 objects. WaTr adds 160 local
values with canonical parents and shared mixture constituents, without registering
children into S223's enum trees. `enums.values` is the complete package index;
an enum object's `children`, `descendants`, and tree browsing describe its
defining package's tree. Use the flat index for extension members. Ancestry and
compatibility checks work across packages.
Generated values retain their defining vocabulary. A WaTr enum on a plain
S223 object selects WaTr's validation shapes and records its import/version;
an explicit water medium also selects water connection and sensor policy.

Registry composition orders dependencies before extensions and selects compatible
views. It supplies hydration symbols, quantity and sensor construction, and mixed
connection policy. Endpoint order does not select the solver's package.
Inherited containment registrations are deduplicated, and matching uses semantic
ancestry so canonical objects remain usable in water assemblies and systems.
S223 connector registrations remain unchanged.

## Pump ancestry and dependency exports

The WaTr closure adds `watr:Pump` as a parent of `s223:Pump`. The generated
`watr.Pump_2` is a view of `s223.Pump` and a subtype of `watr.Pump`. `watr.Pump`
itself still derives from Equipment and accepts the broader Mix-Fluid domain.
S223 Pump and its allowed media remain unchanged. Water graphs retain the
profile parent edge for authoritative validation.

Compiler export format 3 separates new identities from `views`, omits redeclared
aliases/enums, and records the S223 dependency digest. Configuration compilation
consumes selected view metadata without importing generated packages. A dependency
change requires regeneration; conflicting class/enum definitions and unsupported
imported enum hierarchy changes fail explicitly.

`tests/test_watr_linking.py` covers the committed packages: canonical identity,
both import orders, unchanged S223 metadata and enum trees, mixed properties,
containment, connection endpoint orders, class-valued terms, hydration, positive
and negative static typing, and shape-bundle selection. `tests/test_linked_profiles.py`
covers profile-only and transitive restrictions.
