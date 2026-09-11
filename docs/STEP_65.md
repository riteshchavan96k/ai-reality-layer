# Step 65 — Retrieval Provider Request Contract

## Objective

Establish a dedicated, validated provider-facing request contract so retrieval providers receive a stable typed request instead of arbitrary dictionaries.

## Implementation

- Added `RetrievalProviderRequest` as an immutable provider-facing request contract.
- Added validation for query, source type, temporal scope, and required flag.
- Added mapping conversion and serialization boundaries.
- Updated `RetrievalProvider` to accept `RetrievalProviderRequest`.
- Updated `RetrievalProviderExecutor` to execute providers with the typed request while preserving the existing retrieval result envelope.
- Updated `RealityRetrievalEngine` to convert the existing retrieval-contract dictionary into the provider request contract before provider selection/execution.
- Preserved the public retrieval contract shape and existing `RealityRetrievalEngine(provider=...)` construction path.
- Added regression coverage for validation, round-tripping, structural provider compatibility, typed execution, and end-to-end engine conversion.

## Design Boundary

This step is a contract/architecture step. It does not introduce external providers, API keys, credential storage, network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citations, ML training, or LLM integration.

## Validation

Local test execution remains pending because this implementation was performed through GitHub-side repository operations. No GitHub Actions test pass is claimed.
