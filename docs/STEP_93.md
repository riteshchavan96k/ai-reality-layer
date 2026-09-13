# Step 93 — Grounding Context Normalization

## Objective

Establish a canonical normalization boundary for grounding contexts so typed contracts and compatible legacy mappings enter model execution in one stable shape.

## Implementation

- Added `GroundingContextNormalizer`.
- Typed `GroundingContext` instances pass through unchanged.
- Compatible mapping-shaped contexts are converted into the canonical immutable contract.
- Canonical contract validation remains responsible for state, task, source-count, and evidence consistency.
- Malformed source collections and unsupported shapes fail deterministically.
- Preserves `grounding_executed` with an explicit default for legacy mappings.
- Updated orchestration to normalize the builder result before storing grounding state and passing it to execution.
- Added dedicated Step 93 regression coverage.

## Design Boundary

The flow is:

`retrieval result → retrieval consumption → evidence normalization → evidence normalization consumption → evidence quality validation → evidence quality validation result normalization → grounding context contract → grounding context normalization → execution`

Step 93 is a contract-normalization boundary. It does not introduce semantic truth verification, external providers, network access, credentials, RAG, embeddings/vector search, citation generation, ML training, or LLM integration.

## Validation Truth

Dedicated regression tests are included. Local execution has not been performed in this session. No automated test pass is claimed unless an actual test run reports it.
