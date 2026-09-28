# Step 160 — Confidence Signal Contract Validation

## Objective

Harden the existing deterministic confidence-signal boundary immediately after source-freshness validation.

## Why This Is the Correct Next Boundary

The repository already contains `RealityConfidenceSignalResult` and `RealityConfidenceSignalAggregator`. The aggregator consumes evidence quality, claim-evidence coverage, source freshness, and candidate-conflict signals. Step 160 therefore validates that existing result contract instead of inventing a new confidence subsystem.

## Scope

Step 160 validates:

- confidence status;
- evidence usability;
- claim coverage range;
- freshness status;
- conflict count;
- signal collection shape;
- confidence-method identity;
- unavailable-result reasons;
- mapping-to-canonical normalization.

`RealityConfidenceSignalResultNormalizer` accepts either the canonical result or a compatible mapping and routes mapping-shaped results through the canonical validator.

The production `RealityConfidenceSignalAggregator.aggregate_result()` now routes all result-producing paths through the canonical normalizer. Existing deterministic signal semantics are preserved.

## Safety Invariant

retrieval result
→ retrieval validation
→ consumption validation
→ evidence normalization
→ evidence validation
→ evidence consumption validation
→ evidence quality validation
→ claim extraction validation
→ claim-evidence linking validation
→ claim conflict validation
→ source provenance validation
→ source observation validation
→ source freshness validation
→ confidence signal validation

## Semantic Boundary

This is a confidence-signal contract, not a calibrated probability estimate. `supported` and `uncertain` remain deterministic aggregate states derived from existing grounding signals. The system must not present these states as statistical certainty.

Step 160 does not add an LLM judge, embeddings, vector database, new retrieval provider, ML/DL model, model training, or a new truth-verification mechanism.

## Validation Truth

Dedicated Step 160 regression tests cover canonical acceptance, mapping normalization, required-field rejection, invalid coverage/count rejection, aggregator integration, and preservation of uncertainty for partial grounding. Local pytest execution is still required before claiming a local runtime test pass.
