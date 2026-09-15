# Step 102 — Grounding Execution Context Consumption Result Contract

## Objective
Make the result of consuming the grounding execution context an explicit canonical contract.

## Architectural boundary

`grounding execution context → grounding execution context normalization → grounding execution context consumption → grounding execution context consumption result → execution`

## Implementation

Step 101 introduced the consumption decision boundary. Step 102 gives that boundary a dedicated immutable result contract: `GroundingExecutionContextConsumptionResult`.

The contract records:

- `status`: `usable` or `rejected`
- `grounding_status`: `ready` or `not_available`
- `usable`: whether execution may consume the context
- `reason`: explicit rejection reason when unusable
- `consumption_executed`: whether consumption was evaluated

The consumer now returns this canonical result directly.

## Compatibility

The previous `GroundingExecutionContextConsumption` name remains as a compatibility alias so existing Step 101 callers do not break while the canonical result contract is introduced.

## Failure semantics

The contract fails closed on inconsistent states. Usable results cannot contain rejection reasons, while rejected results must provide an explicit reason.

## Scope discipline

This step does not introduce an LLM provider, RAG framework, embeddings, vector database, model training, or external retrieval integration. Those belong at later architectural boundaries when required by the roadmap.

## Validation

Dedicated Step 102 regression tests cover successful and unavailable contexts, execution and preparation rejection, empty ready contexts, contract invariants, invalid grounding states, and deterministic serialization.

Local test execution has not been performed in this session, so no local test pass is claimed.
