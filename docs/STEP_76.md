# Step 76 — Retrieval Provider Health Contract

## Objective

Establish a typed, immutable contract representing the health state of a specific retrieval provider without performing health checks or network calls.

## Implementation

- Adds immutable `RetrievalProviderHealth` identified by provider name.
- Models `healthy`, `unhealthy`, and `unknown` states.
- Preserves stable reasons and explicit health-check state.
- Exposes `is_healthy` for deterministic policy consumption.
- Provides deterministic `to_dict()` serialization.
- Validates provider identity, state, reason, and health-check metadata.
- Keeps health state independent from availability and provider execution.

## Design Boundary

This step establishes the provider-health data contract only. It does not perform health checks, network access, credentials, external-provider calls, availability mutation, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

## Validation Truth

Dedicated Step 76 regression coverage is included. Local execution remains pending unless an actual test run reports success.
