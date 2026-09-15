# Step 106 — Grounding Execution Context Consumption Decision Result Normalization

## Objective

Establish a normalization boundary for the canonical execution-context consumption decision result so downstream execution receives one stable typed representation.

## Architectural boundary

Grounding Execution Context → Consumption → Consumption Result → Consumption Decision → Consumption Decision Result → Consumption Decision Result Normalization → Execution.

## Implementation

`GroundingExecutionContextConsumptionDecisionResultNormalizer` accepts either the canonical typed result or a compatible mapping. Typed results pass through unchanged. Mappings are converted into `GroundingExecutionContextConsumptionDecisionResult`, with semantic consistency enforced by the canonical result contract.

The Step 104 decision evaluator now normalizes the result it produces before returning it, making normalization part of the decision-result boundary without changing existing authorization semantics.

## Failure behavior

Unsupported input shapes are rejected. Invalid mappings are rejected by the canonical result contract, including inconsistent allowed/blocked states, invalid grounding states, and missing reasons for blocked results.

## Scope discipline

This step only establishes the decision-result normalization boundary. It does not introduce external LLM providers, RAG frameworks, embeddings, vector databases, model training, or unrelated infrastructure.

## Validation

Dedicated Step 106 regression tests cover typed pass-through, mapping normalization, blocked-reason preservation, `not_available` state, explicit execution state, invalid mappings, unsupported shapes, invalid grounding state, missing blocked reasons, and deterministic serialization.

Local pytest execution remains pending until the repository is validated on the development machine.
