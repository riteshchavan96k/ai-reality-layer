# Step 111 — Grounding Execution Authorization Consumption Result Contract

## Objective

Make the result produced when grounding execution authorization is consumed an explicit canonical contract.

## Architectural boundary

`grounding execution authorization → authorization result → authorization result normalization → authorization consumption → authorization consumption result → execution`

## Implementation

Step 110 established the authorization-consumption boundary. Step 111 gives that boundary a dedicated immutable result contract: `GroundingExecutionAuthorizationConsumptionResult`.

The contract records:

- `status`: `usable` or `rejected`
- `authorization_status`: `authorized` or `denied`
- `usable`: whether the consumed authorization can permit execution
- `reason`: explicit rejection reason when unusable
- `consumption_executed`: whether consumption was evaluated

The authorization consumer now returns this canonical result directly.

## Compatibility

The previous `GroundingExecutionAuthorizationConsumption` name remains as a backward-compatible alias to the new canonical result contract. Existing Step 110 callers and tests therefore continue to work without maintaining two separate result types.

## Failure semantics

The result contract fails closed on inconsistent states:

- `usable` requires `status="usable"` and `authorization_status="authorized"`.
- `rejected` requires `status="rejected"` and `authorization_status="denied"`.
- Usable results cannot contain a rejection reason.
- Rejected results must contain a non-empty rejection reason.
- `usable` and `consumption_executed` must be booleans.

## Scope discipline

This step introduces no LLM provider, RAG framework, embeddings, vector database, model training, or external retrieval integration. It only formalizes the existing authorization-consumption result boundary.

## Validation

Dedicated Step 111 regression tests cover canonical result typing, authorized and denied results, `not_available` grounding, invalid consumer input, backward-compatible aliasing, contract invariants, invalid authorization state, execution-state typing, and deterministic serialization.

Local pytest execution remains pending; no CI workflow is configured for the repository.
