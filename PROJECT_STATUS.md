# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 80 — Retrieval Provider Selection Policy Result Contract — implementation complete; local validation pending.

### Step 80 Scope

- Adds immutable `RetrievalProviderSelectionPolicyResult` for the combined provider-selection policy decision.
- Represents explicit `allowed` and `rejected` outcomes with source type and stable reason.
- Validates consistency between status and allowed state and provides deterministic serialization.
- Updates `RetrievalProviderSelectionPolicy` and `DefaultRetrievalProviderSelectionPolicy` to return the explicit result contract instead of a bare boolean.
- Preserves fail-closed availability, health, and capability gate semantics and their stable rejection reasons.
- Updates `RegistryRetrievalProviderSelector` to consume the explicit policy result.
- Updates Step 79 regression coverage and adds dedicated Step 80 regression coverage.
- Adds dedicated Step 80 documentation.

### Step 80 Design Boundary

This step formalizes the outcome of combined provider-selection policy evaluation. It does not add external providers, active health probes, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 79 Scope

- Adds `RetrievalProviderSelectionPolicy` as a dedicated policy contract for the combined provider-selection decision.
- Adds deterministic fail-closed policy across availability, health, and capability gates.
- Preserves backward compatibility for providers without capability descriptors.
- Updates provider selection to inject and consult the policy after existing gate-specific checks.
- Adds regression coverage and documentation.

### Step 78 Scope

- Adds immutable `RetrievalProviderHealthEvaluationResult` with explicit healthy, unhealthy, and unknown outcomes.
- Carries provider identity, health status, support state, reason, health-check state, and evaluation execution state.
- Updates health evaluation and provider selection to consume explicit results.
- Adds regression coverage and documentation.

### Step 77 Scope

- Adds dedicated `RetrievalProviderHealthEvaluator`.
- Separates health evaluation from the health state contract.
- Extends registry health registration and lookup.
- Gates provider selection on health after availability and before capability evaluation.
- Adds regression coverage and documentation.

### Step 76 Scope

- Adds immutable `RetrievalProviderHealth` with healthy, unhealthy, and unknown states.
- Preserves stable reasons and explicit health-check state.
- Keeps health state independent from availability and provider execution.
- Adds regression coverage and documentation.

### Step 75 Scope

- Adds immutable `RetrievalProviderAvailabilityEvaluationResult` with explicit available, unavailable, and blocked outcomes.
- Updates availability evaluation and selection to consume explicit results.
- Adds regression coverage and documentation.

### Step 74 Scope

- Adds dedicated `RetrievalProviderAvailabilityEvaluator`.
- Separates availability evaluation from registry lookup and selection orchestration.
- Updates provider selection to delegate availability decisions.
- Adds regression coverage and documentation.

### Step 73 Scope

- Adds immutable `RetrievalProviderAvailability` with available, unavailable, and blocked states.
- Extends registry availability registration and lookup.
- Gates provider selection on availability and preserves backward compatibility.
- Adds regression coverage and documentation.

### Step 72 Scope

- Adds immutable `RetrievalProviderCapabilityEvaluationResult` with explicit supported/unsupported states.
- Updates capability evaluation and selection to consume explicit results.
- Adds regression coverage and documentation.

### Step 71 Scope

- Adds dedicated `RetrievalProviderCapabilityEvaluator`.
- Separates capability-fit evaluation from registry lookup and provider selection.
- Preserves typed request validation and capability mismatch semantics.
- Adds regression coverage and documentation.

### Step 70 Scope

- Adds immutable `RetrievalProviderDescriptor` combining provider identity, implementation, and declared capabilities.
- Extends registry descriptor registration and lookup.
- Updates provider selection to use declared capabilities.
- Preserves legacy providers without descriptors.

### Step 69 Scope

- Adds immutable `RetrievalProviderCapabilities` for supported source types and temporal scopes.
- Normalizes and validates capability declarations and request compatibility.
- Keeps capability description independent from provider execution and selection policy.

### Step 68 Scope

- Adds dedicated `RetrievalResultNormalizer` for stable retrieval-result construction.
- Separates result mapping from provider execution.
- Preserves provider identity, request/source/content/reason, and execution semantics.

### Step 67 Scope

- Adds dedicated `RetrievalProviderResponseNormalizer`.
- Supports typed responses and legacy mappings.
- Rejects unsupported provider-output shapes while preserving retrieval-result semantics.

### Step 66 Scope

- Adds immutable `RetrievalProviderResponse` contract.
- Validates response status, sources, content, provider identity, and reason.
- Updates provider protocol and executor while preserving legacy mappings.

### Step 65 Scope

- Adds immutable `RetrievalProviderRequest` contract.
- Validates query, source type, temporal scope, and required state.
- Updates provider execution to use typed requests while preserving public retrieval contracts.

### Step 64 Scope

- Establishes the canonical runtime-checkable `RetrievalProvider` protocol.
- Updates registry, selection, execution, and engine boundaries to use it.
- Preserves structural provider compatibility and injection behavior.

### Step 63 Scope

- Adds stable `RetrievalProviderSelectionResult` for selected/unavailable outcomes.
- Separates selection results from raw provider objects.
- Makes retrieval execution occur only after successful provider selection.

### Step 62 Scope

- Adds dedicated `RetrievalProviderRegistry` ownership for source-type/provider mappings.
- Separates registration and lookup from selection policy.
- Supports deterministic registration, replacement, normalization, lookup, and default fallback.

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

Steps 54–80 have dedicated regression coverage where documented, but local execution has not been performed in this session. No automated test pass is claimed unless an actual test run reports it.
