# Step 94 — Grounding Context Consumption

## Objective

Establish an explicit consumption boundary that decides whether the canonical grounding context is safe and usable for downstream model execution.

## Implementation

- Added `GroundingContextConsumption`, an immutable consumption decision contract.
- Added `GroundingContextConsumer` for deterministic classification.
- `ready` contexts are usable when they contain evidence content or at least one source.
- Empty `ready` contexts are rejected fail-closed.
- `not_available` contexts remain usable for execution because they explicitly represent the absence of required grounding rather than malformed grounding.
- Updated orchestration dependencies to inject the consumer.
- Updated the pipeline to consume grounding context before execution and record the consumption decision in analysis state.
- Rejected grounding contexts now terminate execution with an explicit `grounding_unavailable` result.
- Added dedicated Step 94 regression coverage.

## Design Boundary

The flow is:

`retrieval → retrieval consumption → evidence normalization → evidence normalization consumption → evidence quality validation → evidence quality validation result normalization → grounding context contract → grounding context normalization → grounding context consumption → execution`

Step 94 does not introduce semantic truth verification, external providers, network access, credentials, RAG, embeddings/vector search, citation generation, ML training, or LLM integration. It establishes the final deterministic acceptance gate for the grounding representation before execution.

## Validation Truth

Dedicated regression tests are included. Local test execution has not been performed in this session. No automated test pass is claimed unless an actual test run reports it.
