# Step 65 — Retrieval Provider Request Contract

## Objective

Establish a dedicated, validated provider-facing request contract so retrieval providers receive a stable typed request instead of arbitrary dictionaries.

## Implementation

- Added immutable `RetrievalProviderRequest` with validation for query, source type, temporal scope, and required state.
- Added mapping conversion and serialization boundaries.
- Updated `RetrievalProvider` to accept `RetrievalProviderRequest`.
- Updated `RetrievalProviderExecutor` to pass validated provider requests while preserving the existing retrieval result envelope.
- Updated `RealityRetrievalEngine` to convert the existing retrieval-contract dictionary into the typed provider request before provider selection and execution.
- Preserved the public retrieval contract shape and existing provider-injection construction path.
- Updated Step 64 regression coverage and added dedicated Step 65 regression coverage.

## Design Boundary

This step is contract/architecture work. It does not introduce external providers, API keys, credential storage, network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citations, ML training, or LLM integration.

## Validation

Local test execution remains pending because this implementation was performed through GitHub-side repository operations. No GitHub Actions test pass is claimed.
