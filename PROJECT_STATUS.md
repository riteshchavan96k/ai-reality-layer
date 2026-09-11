# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 63 — Retrieval Provider Selection Result Contract — implementation complete; local validation pending.

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

### Step 61 Scope

- Adds a provider-neutral `RetrievalProviderSelector` contract for choosing a retrieval provider from a structured retrieval request.
- Adds deterministic registry-based provider selection keyed by retrieval `source_type` with an explicit default provider.
- Updates `RealityRetrievalEngine` to select the provider before delegating execution to the Step 60 provider executor boundary.
- Preserves explicit provider injection behavior by treating an injected provider as the default provider when no selector is supplied.
- Composes and shares the default retrieval provider selector through `OrchestrationDependencies`.
- Preserves Step 55 retrieval result semantics and Step 60 provider execution containment.
- Preserves `not_required` retrieval behavior without invoking provider selection or execution.
- Adds regression coverage for source-type selection, default selection, selected-provider execution, non-execution, and dependency composition.

### Step 61 Design Boundary

This step establishes provider selection as an independent retrieval concern so multiple retrieval implementations can later be introduced without coupling selection policy to retrieval execution. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

### Step 60 Scope

- Adds a provider-neutral `RetrievalProviderExecutor` boundary for retrieval provider execution.
- Moves provider invocation, provider failure containment, blocked/unavailable handling, and malformed provider-output normalization behind the retrieval execution boundary.
- Keeps `RealityRetrievalEngine` responsible for retrieval-contract handling and delegates provider execution to the injected executor.
- Adds retrieval provider executor composition to `OrchestrationDependencies` and shares the composed executor with the default retrieval engine.
- Preserves the stable `RetrievalResultContract` semantics introduced in Step 55.
- Preserves `not_required` retrieval behavior without invoking a provider.
- Adds regression coverage for successful execution, provider failures, malformed output, dependency injection, and non-executed retrieval.

### Step 60 Design Boundary

This step establishes a provider-execution boundary so future retrieval implementations can be introduced without coupling the retrieval engine to provider-specific execution behavior. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

### Step 59 Scope

- Adds an explicit `OrchestrationStageContext` shared by all pipeline stages.
- Makes pipeline state and execution trace available through one named stage context.
- Carries the shared execution budget through the same context used by execution and quality recovery.
- Changes internal stage helpers from positional state/result coordination to context-based mutation.
- Preserves the public `OrchestrationPipeline.run` interface and existing result shapes.
- Preserves routing, retrieval, grounding, execution, evaluation, recovery, fallback, approval, trace, and outcome-memory semantics.
- Adds regression coverage for context state/budget ownership, shared stage mutation, and budget propagation into recovery.

### Step 59 Design Boundary

This step reduces internal coupling between pipeline stages by establishing an explicit stage context contract. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, or ML training.
