# Step 85 — Retrieval Result Consumption

## Objective

Create an explicit boundary between retrieval execution and downstream evidence processing. A retrieval result must be classified as usable or rejected before it is normalized into evidence.

## Implementation

- Added `RetrievalResultConsumption`, an immutable result contract for the consumption decision.
- Added `RetrievalResultConsumer` to validate retrieval status and basic payload usability.
- Integrated the consumer into `OrchestrationDependencies`.
- Updated `OrchestrationPipeline._retrieve_and_ground` to consume retrieval output before evidence normalization.
- Rejected retrieval output is converted into a stable invalid-evidence state and is not passed to the evidence normalizer.
- The consumption decision is preserved in `analysis["reality_retrieval_consumption"]` and the detailed reality-retrieval record.

## Design Boundary

Step 85 does not perform semantic evidence quality scoring, source credibility ranking, freshness evaluation, or LLM reasoning. Those remain separate responsibilities.

The boundary is:

`retrieval result → consumption decision → evidence normalization`

This prevents malformed, empty, failed, blocked, or unsupported retrieval outputs from being silently treated as usable evidence.

## Validation Truth

Dedicated Step 85 regression coverage was added. Local test execution has not been performed in this session, so no local test pass is claimed.
