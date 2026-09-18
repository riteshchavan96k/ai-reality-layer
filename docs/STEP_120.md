# Step 120 — Grounding Execution Authorization Consumption Decision Result Contract

## Objective

Establish the canonical result contract for the final authorization-consumption execution decision produced by Step 119.

## Architectural boundary

Grounding Execution Authorization → Authorization Consumption → Consumption Decision → Decision Result → Decision Result Normalization → Decision Result Consumption → Decision Result Consumption Result → Decision Result Consumption Result Normalization → Decision Result Consumption Result Decision → **Decision Result Contract** → Execution.

## Implementation

Step 120 adds `GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult` as the immutable result contract for the Step 119 final decision.

The result:

- represents allowed or blocked execution states;
- preserves authorization status and rejection reasons;
- validates consistency between status and allowed state;
- validates authorization-state consistency;
- records explicit decision execution state; and
- serializes deterministically through `to_dict()`.

The Step 119 evaluator now returns this canonical result instead of returning the raw decision object.

## Pipeline integration

The orchestration pipeline continues to evaluate the Step 119 decision at the same authorization boundary, but now receives the canonical Step 120 result. The result is recorded in analysis and trace state, and its `allowed` field remains the execution gate.

## Failure behavior

Invalid result states, inconsistent authorization state, invalid reasons, and unsupported conversion inputs fail closed through the canonical contract.

## Scope discipline

This step only formalizes the result contract for the existing final authorization-consumption execution decision. It does not add LLM providers, RAG frameworks, embeddings, vector databases, model training, external retrieval integrations, credentials, or unrelated infrastructure.

## Validation

Dedicated Step 120 regression tests cover allowed and blocked results, reason preservation, invalid states, authorization-state consistency, typed conversion, and deterministic serialization.

GitHub repository status checks are not configured for this project, so no CI test pass is claimed. Local pytest execution remains a separate validation step on the development machine.
