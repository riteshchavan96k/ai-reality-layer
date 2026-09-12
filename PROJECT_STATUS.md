# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 74 — Retrieval Provider Availability Evaluation — implementation complete; local validation pending.

### Step 74 Scope

- Adds dedicated `RetrievalProviderAvailabilityEvaluator` for availability-policy evaluation.
- Separates availability evaluation from registry lookup and provider-selection orchestration.
- Accepts only the typed `RetrievalProviderAvailability` contract and rejects invalid inputs deterministically.
- Updates `RegistryRetrievalProviderSelector` to delegate availability decisions before capability evaluation.
- Preserves stable unavailable selection semantics and existing capability-mismatch behavior.
- Keeps the evaluator injectable so future availability policy can evolve independently.
- Adds dedicated regression coverage for available, unavailable, blocked, invalid input, evaluator delegation, and selection short-circuit behavior.

### Step 74 Design Boundary

This step evaluates already-declared provider availability only. It does not add health checks, network access, credentials, external providers, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 73 Scope

- Adds immutable `RetrievalProviderAvailability` with available, unavailable, and blocked states.
- Preserves stable reasons and explicit availability-check state.
- Extends `RetrievalProviderRegistry` with explicit availability registration and lookup.
- Preserves backward compatibility by treating providers without explicit availability metadata as available.
- Clears stale availability metadata when a source-type provider or descriptor is replaced.
- Updates `RegistryRetrievalProviderSelector` to gate selection on availability before capability evaluation.
- Ensures unavailable or blocked providers are not selected or executed.
- Preserves existing capability-mismatch semantics after availability succeeds.
- Adds dedicated Step 73 regression coverage and documentation.

### Step 73 Design Boundary

This step models provider availability only. It does not add health checks, network access, credentials, external providers, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 72 Scope

- Adds immutable `RetrievalProviderCapabilityEvaluationResult` with explicit supported/unsupported states.
- Carries source type, temporal scope, support state, reason, and evaluation execution state.
- Provides deterministic serialization through `to_dict()`.
- Updates `RetrievalProviderCapabilityEvaluator` to return the result contract instead of a bare boolean.
- Updates `RegistryRetrievalProviderSelector` to consume the explicit evaluation result while preserving capability-mismatch semantics.
- Adds dedicated regression coverage for supported/unsupported results, serialization, and immutability.

### Step 72 Design Boundary

This step formalizes capability-evaluation outcomes only. It does not add external providers, credentials, network access, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 71 Scope

- Adds a dedicated `RetrievalProviderCapabilityEvaluator` for provider/request capability-fit evaluation.
- Separates capability evaluation from registry lookup and provider-selection orchestration.
- Updates `RegistryRetrievalProviderSelector` to delegate capability matching to the evaluator.
- Preserves typed `RetrievalProviderRequest` validation before capability evaluation.
- Preserves stable `retrieval_provider_capability_mismatch` selection semantics.
- Preserves legacy provider registration and selection when no capability descriptor is present.
- Adds regression coverage for compatible requests, source/temporal mismatches, and invalid inputs.

### Step 71 Design Boundary

This step isolates capability-fit evaluation only. It does not execute providers, add external retrieval services, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citations, ML training, or LLM integration.

### Step 70 Scope

- Adds immutable `RetrievalProviderDescriptor` metadata combining provider identity, implementation, and declared capabilities.
- Extends `RetrievalProviderRegistry` with descriptor registration and lookup while preserving legacy registration.
- Updates provider selection to use declared capabilities.
- Converts selection mappings into typed `RetrievalProviderRequest` before capability matching.
- Blocks capability-incompatible requests with stable mismatch semantics without executing providers.
- Preserves legacy providers without descriptors.
- Adds Step 70 regression coverage and documentation.

### Step 69 Scope

- Adds immutable `RetrievalProviderCapabilities` for supported source types and temporal scopes.
- Normalizes capability identifiers and removes duplicates.
- Validates capability declarations.
- Adds typed request compatibility checking and serialization.
- Keeps capability description independent from provider execution and selection policy.
- Adds Step 69 regression coverage and documentation.

### Step 68 Scope

- Adds dedicated `RetrievalResultNormalizer` for stable retrieval-result construction.
- Separates completed/failed/blocked/unavailable mapping from provider execution.
- Preserves provider identity fallback, request/source/content/reason, and execution semantics.
- Adds regression coverage and documentation.

### Step 67 Scope

- Adds dedicated `RetrievalProviderResponseNormalizer`.
- Supports typed responses and legacy mappings.
- Rejects unsupported provider-output shapes.
- Keeps provider execution separate from response normalization.
- Preserves retrieval result semantics and adds regression coverage.

### Step 66 Scope

- Adds immutable `RetrievalProviderResponse` contract.
- Validates response status, sources, content, provider identity, and reason.
- Updates the provider protocol and executor while preserving legacy mappings.
- Adds regression coverage and documentation.

### Step 65 Scope

- Adds immutable `RetrievalProviderRequest` contract.
- Validates query, source type, temporal scope, and required state.
- Updates provider execution to use typed requests while preserving public retrieval contracts.
- Adds regression coverage and documentation.

### Step 64 Scope

- Establishes the canonical runtime-checkable `RetrievalProvider` protocol.
- Updates registry, selection, execution, and engine boundaries to use it.
- Preserves structural provider compatibility and existing injection behavior.
- Adds regression coverage.

### Step 63 Scope

- Adds stable `RetrievalProviderSelectionResult` for selected/unavailable outcomes.
- Separates selection results from raw provider objects.
- Makes retrieval execution occur only after successful provider selection.
- Preserves Step 55/60 semantics and not-required behavior.

### Step 62 Scope

- Adds dedicated `RetrievalProviderRegistry` ownership for source-type/provider mappings.
- Separates registration/lookup from selection policy.
- Supports deterministic registration, replacement, lookup, normalization, and default fallback.

### Step 61 Scope

- Adds provider-neutral retrieval provider selection.
- Uses deterministic source-type selection and explicit default provider.
- Preserves provider injection, execution, result contracts, and not-required behavior.

### Step 60 Scope

- Adds provider-neutral retrieval provider execution boundary.
- Contains provider invocation failures and malformed output.
- Preserves stable retrieval result semantics and not-required behavior.

### Step 59 Scope

- Adds shared `OrchestrationStageContext` for state, trace, and execution budget.
- Preserves public pipeline behavior and shared budget through recovery.

### Step 58 Scope

- Adds explicit `OrchestrationState` for named state across pipeline stages.
- Preserves public orchestration results and existing behavior.

### Step 57 Scope

- Adds `OrchestrationPipeline` and explicit preparation, retrieval/grounding, execution, and evaluation/recovery stages.
- Preserves the public `orchestrate_task` entry point and existing semantics.

### Step 56 Scope

- Adds `OrchestrationDependencies` as the composition and dependency-injection boundary.
- Centralizes default service construction and preserves backward-compatible injection points.

## Validation Truth

Steps 54–74 have dedicated regression coverage where documented, but local execution has not been performed in this session. No automated test pass is claimed unless an actual test run reports it.
