# Reproducible starting inputs

These files freeze the compiler inputs shipped before compiler hardening. Their
SHA-256 hashes and provenance are recorded in `../sources.lock.json`.

- `s223-closure.ttl` and `watr-closure.ttl` are copies of the committed validation
  graphs, not fresh upstream downloads. The WaTr closure includes S223, its QUDT
  3.3.0 imports, and the local ASM2d component additions. Original import document
  boundaries and retrieval dates are unavailable.
- `qudt-catalog.ttl` is a vocabulary projection recovered from the committed QUDT
  3.4.0 Python constants: IRIs, labels, definitions, declared types, and dimension
  vectors. It reproduces those constants exactly; it is not the original QUDT
  distribution and must not be used as its full validation schema.

The WaTr validation closure and the reference catalog deliberately retain their
existing, different QUDT versions. They are separate compilation inputs. A future
source update should capture original documents and their import edges rather
than infer unverified provenance from these graphs.

Ordinary generation is offline (`make regen`); `make regen-check` checks the full
generated file set. To update sources, explicitly acquire and review the new
documents, record their identities, versions, imports, and hashes in the lock,
then regenerate and review the semantic and generated changes. Never refresh
sources implicitly during generation.
