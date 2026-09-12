# Step 73 — Retrieval Provider Availability Contract

## Objective

Introduce an explicit, stable availability contract for retrieval providers so provider capability and provider availability remain separate decisions.

## Implementation

- Added immutable `RetrievalProviderAvailability`.
- Supports `available`, `unavailable`, and `blocked` states.
- Preserves an optional stable reason and an explicit `availability_checked` flag.
- Added deterministic `to_dict()` serialization and `is_available` convenience state.
- Extended `RetrievalProviderRegistry` with explicit availability registration and lookup.
- Preserves backward compatibility by treating providers without explicit availability state as available.
- Clears stale availability metadata when a source-type provider or descriptor is replaced.
- Updated `RegistryRetrievalProviderSelector` to check availability before capability evaluation and provider selection.
- Unavailable or blocked providers are never selected or executed.
- Existing capability-mismatch behavior remains unchanged after availability succeeds.
- Added regression coverage for contract states, validation, registry integration, compatibility defaults, and selector ordering.

## Design Boundary

This step models availability state only. It does not perform health checks, network calls, credentials, external provider integration, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

The intended future architecture is:

`request → provider lookup → availability gate → capability evaluation → selection → execution`

This keeps "can this provider handle the request?" separate from "is this provider currently usable?".

## Validation Truth

Dedicated Step 73 regression coverage has been added. Local execution has not been performed in this session, so no test pass is claimed.
