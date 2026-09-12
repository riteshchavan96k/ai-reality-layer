# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 70 — Retrieval Provider Capability Selection Boundary — implementation complete; local validation pending.

### Step 70 Scope

- Adds an immutable `RetrievalProviderDescriptor` that keeps provider identity, implementation, and declared capabilities together for selection metadata.
- Extends `RetrievalProviderRegistry` with descriptor registration and descriptor lookup while preserving legacy provider registration.
- Updates `RegistryRetrievalProviderSelector` to use declared capabilities when a descriptor is registered.
- Converts the selection mapping into the typed `RetrievalProviderRequest` before capability matching.
- Blocks capability-incompatible requests with stable reason `retrieval_provider_capability_mismatch` without executing the provider.
- Preserves legacy provider selection when a provider has no capability descriptor.
- Adds dedicated Step 70 regression coverage for descriptor metadata, registry composition, compatible selection, capability mismatch, legacy compatibility, and validation.

### Step 70 Design Boundary

This step connects provider capability metadata to provider selection. It does not add provider execution behavior or external retrieval services. It does not add API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

### Step 69 Scope

- Adds an immutable `RetrievalProviderCapabilities` contract for declaring provider-supported source types and temporal scopes.
- Normalizes capability values into deterministic lowercase identifiers and removes duplicates.
- Validates that capability declarations are nonempty and well-formed.
- Adds request compatibility checking against the typed `RetrievalProviderRequest` contract.
- Adds stable dictionary serialization for capability metadata.
- Keeps capability description separate from provider execution and selection policy so future selection can consume capability information without coupling it to provider implementation details.
- Adds dedicated Step 69 regression coverage for normalization, matching, rejection, validation, invalid request types, and serialization.

### Step 69 Design Boundary

This step establishes a provider capability contract so retrieval selection can later reason about provider fit using declared source and temporal support. It does not yet change the provider-selection algorithm or add external retrieval providers. It does not add API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

### Step 68 Scope

- Adds a dedicated `RetrievalResultNormalizer` boundary for converting canonical provider responses into stable retrieval-result envelopes.
- Moves completed, failed, blocked, and provider-unavailable result mapping out of `RetrievalProviderExecutor`.
- Preserves provider identity with an explicit fallback when the provider response omits it.
- Preserves request data, source data, content, reason, and retrieval-executed semantics.
- Rejects non-contract responses at the result-normalization boundary.
- Keeps `RetrievalProviderExecutor` focused on provider invocation, response normalization, and failure containment.
- Adds regression coverage for completed, failed, blocked, unavailable, invalid, and end-to-end executor paths.

### Step 68 Design Boundary

This step separates retrieval-result construction from provider execution so the stable retrieval envelope can evolve independently of provider invocation policy. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

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
