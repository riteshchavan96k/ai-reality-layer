# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 67 — Retrieval Provider Response Normalization — implementation complete; local validation pending.

### Step 67 Scope

- Adds a dedicated `RetrievalProviderResponseNormalizer` boundary for provider output normalization.
- Accepts the typed `RetrievalProviderResponse` contract directly without unnecessary conversion.
- Converts legacy mapping-based provider output through the Step 66 response contract.
- Rejects unsupported provider-output shapes before retrieval-result construction.
- Updates `RetrievalProviderExecutor` to depend on the normalizer rather than owning response-shape conversion logic.
- Preserves completed, failed, blocked, and provider-unavailable result semantics.
- Preserves compatibility with existing dictionary-returning structural providers.
- Adds regression coverage for typed responses, legacy mappings, invalid output, and executor integration.

### Step 67 Design Boundary

This step separates provider-output normalization from provider execution so response-shape compatibility can evolve independently of execution policy. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

### Step 66 Scope

- Adds an immutable `RetrievalProviderResponse` contract for provider output.
- Validates supported response status, source shape, content type, provider identity, and optional reason.
- Supports conversion from existing provider mappings and serialization back to stable dictionaries.
- Updates `RetrievalProvider` to declare the typed response contract.
- Updates `RetrievalProviderExecutor` to normalize typed responses before building the existing retrieval result contract.
- Preserves compatibility with existing dictionary-returning structural providers.
- Updates the unconfigured retrieval provider to return the typed response.
- Adds regression coverage for typed responses, legacy mapping compatibility, invalid responses, and stable failed/blocked semantics.

### Step 66 Design Boundary

This step establishes a typed boundary between retrieval provider implementations and provider execution. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

### Step 65 Scope

- Adds a dedicated immutable `RetrievalProviderRequest` contract for provider-facing retrieval requests.
- Validates query, source type, temporal scope, and required-state fields before provider execution.
- Supports conversion from existing retrieval-contract mappings and serialization back to stable dictionaries.
- Updates `RetrievalProvider` to accept the typed provider request contract.
- Updates `RetrievalProviderExecutor` to pass validated provider requests while preserving the existing retrieval result envelope.
- Updates `RealityRetrievalEngine` to convert the existing retrieval-contract request dictionary into the typed provider request before provider selection and execution.
- Preserves the public retrieval contract shape and existing `RealityRetrievalEngine(provider=...)` construction path.
- Updates Step 64 regression coverage for the typed request boundary and adds dedicated Step 65 regression coverage.

### Step 65 Design Boundary

This step establishes a typed boundary between retrieval orchestration and provider implementations so providers cannot receive an unvalidated arbitrary request shape. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

### Step 64 Scope

- Adds a shared `RetrievalProvider` protocol for all retrieval provider implementations.
- Moves the provider interface out of `RealityRetrievalEngine` into a dedicated retrieval-provider contract module.
- Makes the retrieval provider contract runtime-checkable so implementations can be structurally verified when needed.
- Updates retrieval provider selection results, registry ownership, provider execution, and retrieval engine injection to use the shared provider contract.
- Preserves existing structural provider implementations without requiring inheritance from a concrete base class.
- Preserves Step 63 selection-result semantics and Step 60 provider-execution behavior.
- Preserves the existing `RealityRetrievalEngine(provider=...)` compatibility path.
- Adds regression coverage for valid and invalid provider shapes and end-to-end compatibility through registry, selection result, executor, and engine boundaries.

### Step 64 Design Boundary

This step establishes the canonical interface that every retrieval provider must satisfy before registration, selection, or execution. It reduces type and architectural coupling between retrieval components while keeping providers implementation-agnostic. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

### Step 63 Scope

- Adds a stable `RetrievalProviderSelectionResult` contract for provider-resolution outcomes.
- Separates provider selection results from raw provider objects.
- Represents selected and unavailable provider-resolution states explicitly.
- Carries the resolved source type, provider, reason, and execution-state semantics.
- Updates `RetrievalProviderSelector` and `RegistryRetrievalProviderSelector` to return the stable selection result.
- Updates `RealityRetrievalEngine` to execute only when provider selection succeeds.
- Converts unavailable or malformed selection outcomes into stable non-executing retrieval results.
- Preserves Step 60 provider execution and Step 55 retrieval result contracts.
- Preserves `not_required` retrieval behavior without provider selection or execution.
- Adds regression coverage for selected, unavailable, malformed, and successfully executed selection paths.

### Step 63 Design Boundary

This step establishes a stable contract between retrieval provider selection and provider execution so future selection policies can evolve without exposing raw provider objects as the selector's result protocol. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

### Step 62 Scope

- Adds a dedicated `RetrievalProviderRegistry` boundary for owning source-type-to-provider mappings.
- Separates provider registration and lookup from the Step 61 provider-selection policy.
- Supports deterministic registration, replacement, lookup, and explicit default-provider fallback.
- Normalizes valid source-type keys and rejects invalid empty or non-string source types.
- Updates `RegistryRetrievalProviderSelector` to delegate provider lookup to the dedicated registry.
- Composes and shares the registry through `OrchestrationDependencies` and the retrieval selector/engine graph.
- Updates Step 61 regression coverage to exercise the new registry-backed selector boundary.
- Adds dedicated Step 62 regression coverage for registration, lookup, replacement, normalization, invalid input, and default-provider behavior.
- Preserves retrieval execution, result-contract, not-required, and provider-selection semantics.

### Step 62 Design Boundary

This step establishes provider registry ownership as an independent retrieval concern so provider registration and lookup can evolve without coupling them to selection policy or provider execution. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.
