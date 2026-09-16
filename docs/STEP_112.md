# Step 112 — Grounding Execution Authorization Consumption Result Normalization

## Objective

Establish an explicit normalization boundary between grounding execution authorization consumption and downstream execution gating.

## Boundary

`Grounding Execution Authorization → Authorization Result → Authorization Result Normalization → Authorization Consumption → Authorization Consumption Result → Authorization Consumption Result Normalization → Execution`

## Behavior

`GroundingExecutionAuthorizationConsumptionResultNormalizer` accepts either the canonical typed consumption result or a compatible mapping.

- Typed results pass through unchanged.
- Compatible mappings are converted into `GroundingExecutionAuthorizationConsumptionResult`.
- Optional `reason` and `consumption_executed` values are preserved, with the contract default used for the latter when omitted.
- Required fields remain required.
- Canonical contract validation rejects inconsistent authorization/consumption states rather than repairing them.
- Unsupported input shapes are rejected deterministically.

## Integration

`OrchestrationDependencies` now owns the normalization boundary as an injected dependency. `OrchestrationPipeline` normalizes the raw authorization-consumption result before recording it, tracing it, and deciding whether execution may proceed.

This protects the execution boundary from legacy or alternate consumer implementations that return compatible mappings while preserving the canonical typed result when the normal consumer is used.

## Scope discipline

This step does not introduce an LLM provider, RAG framework, embeddings, vector database, model training, network access, credentials, or unrelated infrastructure. It only formalizes representation normalization at the existing authorization-consumption boundary.

## Compatibility

No existing authorization semantics are changed. The Step 111 canonical result contract remains the source of validation truth, and the existing `GroundingExecutionAuthorizationConsumption` compatibility alias remains available.

## Validation

Dedicated Step 112 regression tests cover typed pass-through, authorized mapping normalization, denial-reason preservation, default and explicit execution-state handling, invalid shapes, missing required fields, inconsistent authorization states, empty rejection reasons, and deterministic serialization.

GitHub repository status checks are not configured for the project, so no CI test pass is claimed. Local pytest execution remains a separate validation step.
