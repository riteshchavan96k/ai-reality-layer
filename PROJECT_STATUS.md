# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 71 — Retrieval Provider Capability Evaluation Contract — implementation complete; local validation pending.

### Step 71 Scope

- Adds a dedicated `RetrievalProviderCapabilityEvaluator` for provider/request capability-fit evaluation.
- Separates capability evaluation from registry lookup and provider-selection orchestration.
- Updates `RegistryRetrievalProviderSelector` to delegate capability matching to the evaluator.
- Preserves typed `RetrievalProviderRequest` validation before capability evaluation.
- Preserves stable `retrieval_provider_capability_mismatch` selection semantics.
- Preserves legacy provider registration and selection when no capability descriptor is present.
- Adds dedicated Step 71 regression coverage for compatible requests, source/temporal mismatches, and invalid inputs.

### Step 71 Design Boundary

This step isolates capability-fit evaluation only. It does not execute providers, add external retrieval services, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

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
