# Step 161 — Reality State Contract Validation

## Objective

Harden the existing final evidence-backed snapshot boundary after Step 160. The `RealityState` object is the canonical deterministic snapshot consumed after confidence-signal aggregation.

## Why This Is the Correct Next Boundary

Steps 154–160 progressively validated claim extraction, claim-evidence linking, claim conflicts, source provenance, source observation, source freshness, and confidence signals. The existing architecture then assembles those already-computed signals into `RealityState`. Step 161 therefore validates that final internal snapshot without introducing a new product subsystem.

## Scope

Step 161 validates:

- allowed state status;
- non-empty task identity;
- all required snapshot dictionaries;
- assembly-method identity;
- unavailable-state reasons;
- reason/status consistency;
- mapping-shaped state normalization.

The existing immutable `RealityState` dataclass remains the canonical representation. `RealityStateNormalizer` accepts either the canonical value or a compatible mapping and routes mappings through canonical validation.

`RealityStateBuilder.build_result()` now routes its assembled state through the canonical normalization boundary. Existing deterministic assembly semantics are unchanged.

## Safety Invariant

retrieval validation
→ evidence validation
→ claim extraction validation
→ claim-evidence linking validation
→ claim conflict validation
→ source provenance validation
→ source observation validation
→ source freshness validation
→ confidence signal validation
→ Reality State validation

## Semantic Boundary

A `RealityState` is an evidence-backed system snapshot of signals and their current statuses. `supported` is a deterministic grounding state, not a calibrated probability or proof of truth. Step 161 does not introduce an LLM judge, embeddings, vector databases, new retrieval providers, ML/DL models, model training, or a new truth-verification mechanism.

## Validation

Dedicated Step 161 tests cover canonical acceptance, mapping normalization, missing fields, malformed snapshot fields, unavailable-state reason enforcement, and production builder integration. Local pytest execution is required before claiming a local runtime test pass.
