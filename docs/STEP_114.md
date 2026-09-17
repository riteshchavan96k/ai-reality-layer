# Step 114 — Grounding Execution Authorization Consumption Decision Result Contract

## Objective

Make the grounding execution authorization consumption decision a canonical typed result before model execution proceeds.

## Architectural boundary

Grounding Execution Authorization → Authorization Consumption → Consumption Result → Consumption Decision → Consumption Decision Result → Execution.

## Implementation

`GroundingExecutionAuthorizationConsumptionDecisionResult` is an immutable result contract containing:

- `status` (`allowed` or `blocked`);
- `authorization_status` (`authorized` or `denied`);
- `allowed` execution state;
- an optional rejection reason; and
- explicit `decision_executed` state.

The contract validates state consistency and provides deterministic serialization through `to_dict()`.

The Step 113 decision evaluator now converts the canonical `GroundingExecutionAuthorizationConsumptionDecision` into this result contract. Existing authorization-consumption decision semantics are preserved; the downstream pipeline receives the explicit typed result shape.

## Failure behavior

Allowed results require `allowed=True` and no reason. Blocked results require `allowed=False` and a non-empty reason. Authorization status must agree with the allowed state, and invalid execution-state values are rejected.

## Scope discipline

This step only establishes the result contract boundary already implied by Step 113. It does not introduce an LLM provider, RAG framework, embeddings, vector database, model training, external retrieval integration, credentials, or unrelated infrastructure.

## Validation

Dedicated Step 114 regression tests cover canonical result creation, evaluator conversion, authorization-status preservation, blocked-reason preservation, invalid decision input, state consistency, explicit decision execution state, and deterministic serialization.

GitHub repository status checks are not configured for the project, so no CI test pass is claimed. Local pytest execution remains a separate validation step on the development machine.
