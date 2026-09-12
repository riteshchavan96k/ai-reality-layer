# Step 77 — Retrieval Provider Health Contract

## Objective

Establish a typed, immutable contract for provider health without performing health checks or network calls.

## Implementation

- Adds `RetrievalProviderHealth` with `healthy`, `unhealthy`, and `unknown` states.
- Preserves stable reasons and explicit health-check state.
- Provides deterministic serialization through `to_dict()`.
- Keeps health state independent from availability and provider execution.

## Design Boundary

This step models provider health only. It does not perform health checks, network access, credentials, external-provider calls, availability mutation, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

## Validation Truth

Dedicated Step 77 regression coverage is required. Local execution remains pending unless an actual test run reports success.
