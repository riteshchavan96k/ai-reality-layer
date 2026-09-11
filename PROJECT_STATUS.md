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

This step reduces internal coupling between pipeline stages by establishing an explicit stage context contract. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, or ML training.

### Step 58 Scope

- Adds an explicit `OrchestrationState` contract for state carried across pipeline stages.
- Replaces positional stage-state coordination in `OrchestrationPipeline.run` with named state fields.
- Centralizes task, analysis, routing, approval, retrieval, evidence, grounding, execution, evaluation, recovery, and outcome state.
- Provides named accessors for the retrieval contract and final execution result.
- Preserves the existing public orchestration result shape and functional pipeline behavior.
- Preserves Step 56 dependency injection and Step 57 stage boundaries.
- Adds regression coverage for state defaults, named state access, and pipeline result compatibility.

### Step 58 Design Boundary

This step reduces internal state-coupling between orchestration stages and establishes a stable state contract for future pipeline evolution. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training.

### Step 57 Scope

- Adds an explicit `OrchestrationPipeline` boundary around the existing orchestration sequence.
- Decomposes the large orchestration function into explicit preparation/approval, retrieval/grounding, execution, and evaluation/recovery stages.
- Keeps the public `orchestrate_task` entry point stable while delegating pipeline execution to the new boundary.
- Preserves dependency injection introduced in Step 56.
- Preserves the shared execution budget across primary execution and quality recovery.
- Preserves existing routing, retrieval, grounding, evaluation, recovery, trace, outcome-memory, fallback, and approval semantics.
- Adds regression coverage for stage execution, shared budget propagation, and approval blocking before retrieval.

### Step 57 Design Boundary

This step reduces procedural coupling in the orchestration entry point without changing the pipeline's functional behavior. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

### Step 56 Scope

- Adds an explicit `OrchestrationDependencies` composition boundary for services used by the orchestration pipeline.
- Centralizes construction of the default orchestration service graph in one dependency-composition object.
- Allows `orchestrate_task` callers to inject service implementations without changing the existing pipeline behavior.
- Removes direct construction of retrieval, evidence, grounding, approval, and provider-execution services from the orchestration function body.
- Preserves the existing optional `approval_policy` and `retrieval_engine` injection points for backward compatibility.
- Adds regression coverage for the default dependency graph and injected-service orchestration behavior.
- Does not redesign the pipeline sequence or change existing execution, retrieval, grounding, evaluation, recovery, trace, or outcome-memory semantics.

### Step 56 Design Boundary

This step establishes dependency composition and injection needed before further orchestration decomposition. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, semantic evaluation, citation generation, latency optimization, or ML training.
