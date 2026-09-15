# Step 110 — Grounding Execution Authorization Consumption

## Objective

Establish an explicit consumption boundary between the canonical grounding execution authorization result and model execution.

## Boundary

Grounding Execution Authorization → Authorization Result → Authorization Result Normalization → Authorization Consumption → Execution.

## Behavior

`GroundingExecutionAuthorizationConsumer` accepts only the canonical `GroundingExecutionAuthorizationResult`.

Authorized results are consumed as usable execution authorization. Denied results are consumed as rejected authorization while preserving the upstream denial reason.

The consumer does not reinterpret raw mappings. Representation normalization belongs to the preceding normalization boundary.

## Integration

The orchestration pipeline records authorization consumption in analysis and trace state and blocks execution when the consumed authorization is rejected. Model execution is entered only after this consumption boundary reports a usable result.

## Scope discipline

This step intentionally does not introduce LLM providers, RAG frameworks, embeddings, vector databases, model training, or unrelated infrastructure. Those capabilities will be introduced at the appropriate intelligence boundary.

## Validation

Dedicated Step 110 regression tests cover authorized and denied results, not-available grounding, invalid input, reason preservation, execution state, contract consistency, and deterministic serialization.

Local pytest execution remains pending; no CI workflow is configured for the repository.
