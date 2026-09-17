# Step 115 — Grounding Execution Authorization Consumption Decision Result Normalization

## Objective

Normalize the grounding execution authorization consumption decision result at the orchestration boundary before execution is allowed to proceed.

## Architectural boundary

Grounding Execution Authorization → Authorization Consumption → Consumption Result → Consumption Decision → Decision Result → **Decision Result Normalization** → Execution.

## Implementation

`GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer` is the canonical normalization boundary for the Step 114 result contract.

It:

- preserves an existing `GroundingExecutionAuthorizationConsumptionDecisionResult` instance unchanged;
- converts mapping-shaped results into the canonical immutable result contract;
- preserves status, authorization status, allowed state, reason, and decision execution state; and
- relies on the canonical result contract to reject inconsistent or invalid states.

The orchestration dependency graph now owns this normalizer, and the pipeline normalizes the evaluator output before storing the decision in analysis, tracing it, and using its `allowed` state as the execution gate.

## Failure behavior

Unsupported values are rejected. Mapping values with missing required fields or inconsistent authorization/allowed state are rejected by the canonical result contract rather than silently repaired.

## Scope discipline

This step only establishes the normalization boundary implied by Step 114. It does not introduce an LLM provider, RAG framework, embeddings, vector database, model training, external retrieval integration, credentials, or unrelated infrastructure.

## Validation

Dedicated Step 115 regression tests cover typed-result pass-through, mapping normalization, reason preservation, explicit decision state, invalid status/state combinations, non-mapping rejection, missing blocked reason, and deterministic serialization.

GitHub repository status checks are not configured for this project, so no CI test pass is claimed. Local pytest execution remains a separate validation step on the development machine.
