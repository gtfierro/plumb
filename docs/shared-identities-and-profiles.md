# Shared ontology identities and model profiles

Decision: use canonical dependency classes and model-scoped SHACL profiles.
The integration prototype is implemented; migration of the committed WaTr
package is a separate step. This decision narrows that migration's contract
rather than claiming it is complete.

## Identity and public imports

S223 owns its Python classes and enumeration values. An extension includes
these exact objects in its registry and declares local subclasses for its own
ontology terms. Import canonical classes from `plumb.s223` and extension terms
from their defining package. A subclass remains a nominal Python subtype, so
runtime and static range checks agree. Do not create parallel class definitions
or a second enumeration tree merely because a dependency occurs in a closure.

The executable prototype in `tests/test_linked_profiles.py` uses the real S223
package as a dependency and compiles a small water extension. It exercises
canonical identity, subtype checks, both import orders, containment, connection
resolution, hydration, and positive/negative static typing. It does not replace
the committed `plumb.watr` package.

## Profile constraints

An extension may put a SHACL shape on an imported class. That shape constrains
the model graph when the extension is selected. It does not modify the shared
class, install descriptors globally, change the defining registry, or alter its
constructor defaults. Such constraints are reported as profile constraints
enforced by SHACL validation. A canonical constructor can therefore accept a
value that a selected profile later rejects; `Model.compile()` validates the
finished model by default.

For example, the prototype limits the value of every quantifiable observable
property to 100 in a model using the water extension. A shared S223 property
with value 120 remains valid in a plain S223 model and fails validation in the
water model, regardless of which package was imported first. The restriction
also applies to imported instances, not only extension subclasses.

Ordinary authored models select extension shapes through their generated local
classes. Hydration also retains the registries explicitly selected by
`Model.from_graph(..., registries=...)`, even if the graph contains only shared
class instances. Selection and dependency shapes survive snapshot creation.
Transitive profiles compose by conjunction; there is no import-order winner.
Validation loads each selected shape bundle once, preserving anonymous SHACL
lists rather than duplicating them through both registry and file loading.
Importing a module alone does not activate its profile in unrelated models.
For a custom profile with no local instances, use the existing explicit
hydration registry argument. A graph without an installed package mapping must
still supply that registry when loaded again.

Class-valued links resolve against the selected model's symbols, since a base
registry cannot know future extension classes. Hydration does not add those
classes to the dependency's registry. Conflicting class identities are rejected.
Hydration preserves invalid graphs for inspection; profile validity is checked
by `validate()` or `compile()`, not by inventing replacement values on load.

An imported class cannot silently acquire new RDF parents or a new Python
name. Imported authoring defaults cannot silently change its constructor.
The extension compiler rejects these attempts with the target and source;
declare a local subclass for a separate constructive authoring projection.

## What the actual WaTr migration must handle

The pinned closures share 181 class IRIs. Comparing semantic constraints,
rather than Python aliases and anonymous source labels, reveals additions:

- WaTr adds `hasProcess` and `hasTreatmentObjective` to 123 imported classes.
- It adds `hasMeasurementRange` to 21 imported sensor classes and additional
  measurement metadata to the three quantifiable property classes.
- Its closure adds `watr:Pump` as a parent of `s223:Pump` and adds an inverse
  for QUDT's `hasUnit` projection.

These changes cannot be handled by discarding every repeated class definition
and assuming their authoring surfaces are identical. The migration must decide
how to expose the added properties on imported terms and represent the Pump
ancestry change. New enum branches and adapter policy also need extension-local
selection without mutating dependency enum trees or connector registrations;
the prototype covers imported enum identity and the existing S223 backend.
If typed Python views are necessary, they need explicit
canonical identity, registry selection, hydration, and profile semantics before
they are generated. This prototype deliberately does not introduce an untested
view mechanism or modify the pinned ontology to conceal those differences.

Acceptance for migration remains the full phase 4 matrix in
[the hardening plan](compiler-hardening-plan.md): mixed properties, containment,
connections, class-valued terms, enums, hydration, typing, and deterministic
shape selection against the actual WaTr package.
