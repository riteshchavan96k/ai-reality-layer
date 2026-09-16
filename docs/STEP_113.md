# Step 113 — Grounding Execution Authorization Consumption Decision

## Objective

Establish a dedicated execution decision boundary after grounding execution authorization consumption and before model execution.

## Architectural boundary

`grounding execution authorization → authorization consumption → consumption result → consumption-result normalization → consumption decision → execution`

## Implementation

Step 113 adds `GroundingExecutionAuthorizationConsumptionDecision` and `GroundingExecutionAuthorizationConsumptionDecisionEvaluator`.

The decision is derived only from the canonical `GroundingExecutionAuthorizationConsumptionResult`:

- usable authorization consumption produces an allowed decision;
- rejected authorization consumption produces a blocked decision and preserves its rejection reason;
- authorization status is preserved in the decision;
- invalid evaluator input is rejected rather than coerced; and
- inconsistent decision state is rejected by the canonical decision contract.

The orchestration dependency graph exposes the evaluator explicitly. The pipeline records the decision in analysis and trace state and uses the decision, rather than the raw authorization-consumption result, as the execution gate.

## Failure behavior

A blocked authorization-consumption decision prevents model execution and uses the existing `execution_context_unavailable` result path. Decision state is recorded before the block so the authorization status and rejection reason remain observable.

## Scope discipline

This step does not introduce an LLM provider, RAG framework, embeddings, vector database, model training, external retrieval integration, credentials, or unrelated infrastructure. It formalizes the decision boundary already implied by the authorization-consumption contract.

## Compatibility

Step 112 remains the normalization boundary for the consumption result. Step 113 consumes that canonical normalized result and does not change the underlying authorization or consumption semantics.

## Validation

Dedicated Step 113 regression tests cover allowed and blocked decisions, authorization-status and reason preservation, invalid input, state consistency, explicit decision execution state, and deterministic serialization.

GitHub repository status checks are not configured for the project, so no CI test pass is claimed. Local pytest execution remains a separate validation step.
