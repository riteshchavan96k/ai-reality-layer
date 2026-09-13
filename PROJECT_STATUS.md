# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 79 — Retrieval Provider Selection Policy Contract — implementation complete; local validation pending.

### Step 79 Scope

- Adds `RetrievalProviderSelectionPolicy` as a dedicated policy contract for the combined provider-selection decision.
- Adds `DefaultRetrievalProviderSelectionPolicy` with deterministic fail-closed gate semantics.
- Requires availability and health evaluation results to be supported.
- Requires capability evaluation to be supported when capability metadata exists.
- Preserves backward compatibility for providers without capability descriptors.
- Updates `RegistryRetrievalProviderSelector` to inject and consult the selection policy after existing gate-specific checks.
- Preserves existing availability, health, and capability rejection semantics.
- Uses stable `retrieval_provider_selection_policy_rejected` when the injected final policy rejects an otherwise eligible provider.
- Adds regression coverage for policy contract conformance, supported/unsupported gates, invalid inputs, backward compatibility, and selector integration.
- Adds dedicated Step 79 documentation.

### Step 79 Design Boundary

This step separates combined provider-selection policy from individual availability, health, and capability evaluation mechanisms. It does not add external providers, active health probes, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 78 Scope

- Adds immutable `RetrievalProviderHealthEvaluationResult` with explicit healthy, unhealthy, and unknown outcomes.
- Carries provider identity, health status, support state, reason, health-check state, and evaluation execution state.
- Enforces consistency between health status and `supported`.
- Provides deterministic serialization.
- Updates `RetrievalProviderHealthEvaluator` to return the explicit result contract.
- Updates `RegistryRetrievalProviderSelector` to consume health evaluation results.
- Adds dedicated regression coverage and documentation.

### Step 78 Design Boundary

This step formalizes health-evaluation outcomes only. It does not perform active health probes, network access, credentials, external-provider calls, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 77 Scope

- Adds dedicated `RetrievalProviderHealthEvaluator` for provider-health evaluation.
- Separates health evaluation from the `RetrievalProviderHealth` state contract.
- Evaluates healthy providers as eligible and unhealthy or unknown providers as ineligible.
- Extends `RetrievalProviderRegistry` with explicit health registration and lookup.
- Preserves backward compatibility by treating providers without explicit health metadata as healthy.
- Updates `RegistryRetrievalProviderSelector` to gate selection on health after availability and before capability evaluation.
- Adds regression coverage and documentation.

### Step 76 Scope

- Adds immutable `RetrievalProviderHealth` identified by provider name.
- Models healthy, unhealthy, and unknown states.
- Preserves stable reasons and explicit health-check state.
- Provides deterministic serialization and validation.
- Keeps health state independent from availability and provider execution.
- Adds dedicated regression coverage and documentation.

### Step 75 Scope

- Adds immutable `RetrievalProviderAvailabilityEvaluationResult` with explicit available, unavailable, and blocked outcomes.
- Carries availability reason and availability-check state into a stable evaluation result.
- Updates the availability evaluator and selector to consume the explicit result.
- Adds dedicated regression coverage and documentation.

### Step 74 Scope

- Adds dedicated `RetrievalProviderAvailabilityEvaluator`.
- Separates availability evaluation from registry lookup and selection orchestration.
- Updates the selector to delegate availability decisions before capability evaluation.
- Preserves stable unavailable selection semantics.
- Adds regression coverage and documentation.

### Step 73 Scope

- Adds immutable `RetrievalProviderAvailability` with available, unavailable, and blocked states.
- Extends the registry with explicit availability registration and lookup.
- Preserves backward compatibility by treating providers without explicit availability metadata as available.
- Updates selection to gate on availability.
- Adds regression coverage and documentation.

### Step 72 Scope

- Adds immutable `RetrievalProviderCapabilityEvaluationResult` with explicit supported/unsupported states.
- Carries source type, temporal scope, support state, reason, and evaluation execution state.
- Updates capability evaluation and selection to consume the explicit result.
- Adds regression coverage and documentation.

### Step 71 Scope

- Adds a dedicated `RetrievalProviderCapabilityEvaluator`.
- Separates capability-fit evaluation from registry lookup and provider selection.
- Preserves typed request validation, capability mismatch semantics, and legacy providers without descriptors.
- Adds regression coverage and documentation.

### Step 70 Scope

- Adds immutable `RetrievalProviderDescriptor` combining provider identity, implementation, and declared capabilities.
- Extends the registry with descriptor registration and lookup.
- Updates provider selection to use declared capabilities.
- Blocks capability-incompatible requests without executing providers.
- Preserves legacy providers without descriptors.

### Step 69 Scope

- Adds immutable `RetrievalProviderCapabilities` for supported source types and temporal scopes.
- Normalizes capability identifiers and removes duplicates.
- Validates capability declarations and request compatibility.
- Keeps capability description independent from provider execution and selection policy.

### Step 68 Scope

- Adds dedicated `RetrievalResultNormalizer` for stable retrieval-result construction.
- Separates completed, failed, blocked, and unavailable mapping from provider execution.
- Preserves provider identity, request/source/content/reason, and execution semantics.

### Step 67 Scope

- Adds dedicated `RetrievalProviderResponseNormalizer`.
- Supports typed responses and legacy mappings.
- Rejects unsupported provider-output shapes while preserving retrieval-result semantics.

### Step 66 Scope

- Adds immutable `RetrievalProviderResponse` contract.
- Validates response status, sources, content, provider identity, and reason.
- Updates the provider protocol and executor while preserving legacy mappings.

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

Steps 54–79 have dedicated regression coverage where documented, but local execution has not been performed in this session. No automated test pass is claimed unless an actual test run reports it.
