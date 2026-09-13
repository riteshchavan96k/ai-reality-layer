# Step 86 — Retrieval Result Consumption Normalization

## Objective

Establish a canonical normalization boundary for retrieval-consumption decisions before the orchestration pipeline uses those decisions to control evidence processing.

## Implementation

- Added `RetrievalResultConsumptionNormalizer`.
- Typed `RetrievalResultConsumption` instances pass through unchanged.
- Compatible mapping-shaped consumption decisions are converted into the typed contract.
- Missing optional fields use the contract defaults.
- Invalid or unsupported shapes are rejected deterministically.
- Integrated the normalizer into `OrchestrationDependencies`.
- Updated `OrchestrationPipeline` to normalize the consumer output before checking usability or recording consumption state.

## Design Boundary

The boundary is:

`retrieval result → consumption decision → consumption normalization → evidence processing`

This keeps retrieval-result classification separate from evidence normalization. The normalizer does not perform retrieval, provider selection, evidence scoring, grounding, or model reasoning.

## Compatibility

The existing `RetrievalResultConsumer` already returns the canonical typed contract. Step 86 additionally protects the orchestration boundary from legacy or alternate consumer implementations that return compatible mappings.

## Validation Truth

Dedicated Step 86 regression tests cover typed pass-through, mapping normalization, rejection reasons, defaults, invalid mappings, inconsistent state, unsupported shapes, and deterministic serialization.

Local execution has not been performed in this session, so no test pass is claimed.
