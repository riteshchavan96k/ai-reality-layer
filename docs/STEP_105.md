# Step 105 — Grounding Execution Context Consumption Decision Result Contract

## Objective

Make the execution-context consumption decision a canonical typed result before execution proceeds.

## Architectural boundary

Grounding Execution Context → Consumption → Consumption Result → Consumption Decision → Consumption Decision Result → Execution.

## Implementation

`GroundingExecutionContextConsumptionDecisionResult` is an immutable contract containing status, grounding status, execution authorization, an optional rejection reason, and decision execution state. It validates consistency and provides deterministic serialization.

The decision evaluator now converts the canonical Step 104 decision into this result contract. Existing decision semantics are preserved, while downstream consumers receive one explicit result shape.

## Failure behavior

Allowed results require `allowed=True` and no reason. Blocked results require `allowed=False` and a non-empty reason. Invalid grounding states and execution-state values are rejected.

## Scope discipline

This step only establishes the contract boundary. It does not introduce external LLM providers, RAG frameworks, embeddings, vector databases, model training, or unrelated infrastructure.

## Validation

Dedicated Step 105 regression tests cover canonical result creation, decision conversion, blocked reasons, `not_available` state, invalid states, explicit execution state, and deterministic serialization.

Local pytest execution remains pending until the repository is validated on the development machine.
