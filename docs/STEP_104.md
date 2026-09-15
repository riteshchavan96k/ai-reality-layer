# Step 104 — Grounding Execution Context Consumption Decision

## Objective

Establish a dedicated decision boundary after grounding execution context consumption and before model execution.

## Architectural boundary

`grounding execution context → normalization → consumption → consumption result → consumption decision → execution`

## Implementation

Step 104 adds `GroundingExecutionContextConsumptionDecision` and `GroundingExecutionContextConsumptionDecisionEvaluator`.

The decision is derived only from the canonical `GroundingExecutionContextConsumptionResult`:

- usable consumption produces an allowed decision;
- rejected consumption produces a blocked decision and preserves its reason;
- `not_available` remains allowed when the consumption result is explicitly usable; and
- invalid evaluator input is rejected rather than coerced.

The orchestration dependency graph exposes the evaluator explicitly. The pipeline records the decision in analysis and trace state and uses the decision, rather than the raw consumption object, as the final execution authorization at this boundary.

## Failure behavior

A blocked decision prevents model execution and returns the existing `execution_context_unavailable` result path. Decision state is recorded before the block so the reason remains observable.

## Scope discipline

This step intentionally does not introduce an LLM provider, RAG framework, embeddings, vector database, model training, or external retrieval integration. Those capabilities belong at later intelligence boundaries.

## Validation

Dedicated Step 104 regression tests cover allowed and blocked decisions, `not_available` behavior, invalid inputs, state consistency, explicit execution state, and deterministic serialization.

Local pytest execution has not been performed in this session, so no local test pass is claimed.
