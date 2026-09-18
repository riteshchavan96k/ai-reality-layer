# Current Status — Step 129

## Step 129 — Source Freshness Evaluation Boundary

**Status:** Implementation complete on branch `step-129-freshness-evaluation-boundary`; PR/merge pending.

Step 129 adds an explicit source-freshness evaluation boundary after source observation metadata. It introduces immutable freshness assessment/result contracts, an injectable-clock evaluator, an explicit optional freshness window on retrieval requests, pipeline/dependency integration, regression coverage, and dedicated documentation.

**Semantic boundary:** Missing freshness windows produce `unknown`, not `fresh`. The implementation measures observation recency only; it does not infer publication/update freshness or factual truth.

**Validation truth:** GitHub status checks are not configured. No CI or local pytest pass is claimed in this session; local pytest execution remains required.


# Current Status — Step 128

## Step 128 — Source Observation Metadata Boundary

**Status:** Complete and merged into `main` via PR #134.

Step 128 records when each identified evidence source was observed by the retrieval pipeline. It adds immutable source-observation contracts, timezone-aware ISO-8601 timestamps, an injectable clock, fail-closed propagation, and pipeline/dependency integration.

Dedicated Step 128 regression coverage and docs/STEP_128.md are included.

**Validation truth:** GitHub status checks are not configured. No CI or local pytest pass is claimed in this session; local pytest execution remains required.


# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 87 — Evidence Normalization Contract — implementation complete; local validation pending.

### Step 87 Scope

- Adds immutable `EvidenceNormalizationResult` as the canonical contract for normalized retrieval evidence.
- Captures normalized evidence status, provenance-preserving sources, content, source count, content presence, and normalization execution state.
- Validates consistency between source count, source collection, and content-presence state.
- Adds `RetrievalEvidenceNormalizer.normalize_result()` as the typed normalization boundary.
- Preserves the existing `normalize()` dictionary API for backward compatibility.
- Updates `OrchestrationPipeline` to consume the typed evidence normalization result before downstream evidence-quality validation and grounding.
- Adds dedicated Step 87 regression coverage and documentation.

### Step 87 Design Boundary

This step establishes the boundary `retrieval result → evidence normalization result contract → evidence quality validation`. It does not add external providers, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 86 Scope

- Adds `RetrievalResultConsumptionNormalizer` as the canonical normalization boundary for retrieval-consumption decisions.
- Preserves typed `RetrievalResultConsumption` instances without rebuilding them.
- Converts compatible legacy mapping-shaped consumption decisions into the canonical contract.
- Preserves optional contract defaults and deterministic validation.
- Integrates normalization into `OrchestrationDependencies`.
- Updates `OrchestrationPipeline` to normalize consumer output before usability checks and evidence processing.
- Adds dedicated Step 86 regression coverage and documentation.

### Step 86 Design Boundary

This step establishes the boundary `retrieval result → consumption decision → consumption normalization → evidence processing`. It does not add external providers, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 85 Scope

- Adds immutable `RetrievalResultConsumption` as the stable decision contract between retrieval execution and evidence processing.
- Adds `RetrievalResultConsumer` to classify completed, failed, blocked, not-required, malformed, empty, and unsupported retrieval outputs.
- Integrates the consumer into `OrchestrationDependencies`.
- Updates `OrchestrationPipeline._retrieve_and_ground` so rejected retrieval results are not passed to evidence normalization.
- Preserves the consumption decision in the orchestration analysis/reality-retrieval record.
- Keeps semantic evidence quality scoring separate from retrieval-result consumption.
- Adds dedicated Step 85 regression coverage and documentation.

### Step 85 Design Boundary

This step establishes the boundary `retrieval result → consumption decision → evidence normalization`. It does not add external providers, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 84 Scope

- Makes `RealityRetrievalEngine` consume the canonical `RetrievalProviderSelectionResultNormalizer` boundary before provider execution.
- Preserves typed selection results without rebuilding them.
- Converts compatible legacy selected/unavailable mappings before execution decisions are made.
- Normalizes nested selection decisions through the existing Step 82 boundary.
- Fails closed with `invalid_provider_selection_result` for invalid or unsupported selector outputs.
- Preserves the rule that provider execution occurs only after a normalized selected result.
- Preserves the existing `not_required` retrieval path.
- Adds dedicated Step 84 regression coverage and documentation.

### Step 84 Design Boundary

This step establishes the consumption boundary between provider selection and retrieval execution. It does not add external providers, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 83 Scope

- Adds `RetrievalProviderSelectionResultNormalizer` as the canonical selection-result normalization boundary.
- Accepts typed selection results without rebuilding them.
- Converts compatible legacy selected/unavailable mappings into the canonical result contract.
- Delegates nested decision normalization to `RetrievalProviderSelectionDecisionNormalizer`.
- Preserves provider objects and stable rejection reasons.
- Rejects unsupported result shapes and invalid mappings deterministically.
- Adds dedicated Step 83 regression coverage and documentation.

### Step 83 Design Boundary

This step establishes selection-result normalization only. It does not add external providers, network access, credentials, active health probes, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 82 Scope

- Adds `RetrievalProviderSelectionDecisionNormalizer` as the canonical decision normalization boundary.
- Accepts typed decisions without rebuilding them.
- Converts compatible legacy mappings into the canonical decision contract.
- Normalizes embedded policy-result mappings into `RetrievalProviderSelectionPolicyResult`.
- Updates `RetrievalProviderSelectionResult` to normalize and validate attached decisions.
- Enforces consistency between result status and decision status.
- Adds dedicated Step 82 regression coverage and documentation.

### Step 82 Design Boundary

This step establishes decision normalization only. It does not add external providers, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 81 Scope

- Adds immutable `RetrievalProviderSelectionDecision` for the final provider-selection outcome.
- Represents explicit selected and rejected decisions.
- Preserves source type, selected provider when applicable, rejection reason, and the policy result.
- Validates consistency between decision status and provider presence.
- Provides deterministic serialization through `to_dict()`.
- Adds dedicated regression coverage and documentation.

### Step 81 Design Boundary

This step formalizes the final provider-selection decision record. It does not add external providers, active health probes, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

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
- Provides deterministic `to_dict()` serialization.
- Updates `RetrievalProviderHealthEvaluator` to return the explicit result contract instead of a bare boolean.
- Updates `RegistryRetrievalProviderSelector` to consume `health_evaluation.supported` while preserving existing selection semantics.
- Updates Step 77 regression coverage for the new evaluator return contract.
- Adds dedicated Step 78 regression coverage and documentation.

### Step 78 Design Boundary

This step formalizes health-evaluation outcomes only. It does not perform active health probes, network access, credentials, external-provider calls, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 77 Scope

- Adds dedicated `RetrievalProviderHealthEvaluator` for provider-health evaluation.
- Separates health evaluation from the `RetrievalProviderHealth` state contract.
- Evaluates healthy providers as eligible and unhealthy or unknown providers as ineligible.
- Rejects invalid health inputs deterministically.
- Extends `RetrievalProviderRegistry` with explicit health registration and lookup.
- Preserves backward compatibility by treating providers without explicit health metadata as healthy.
- Clears stale health metadata when a source-type provider or descriptor is replaced.
- Updates `RegistryRetrievalProviderSelector` to gate selection on health after availability and before capability evaluation.
- Keeps the health evaluator injectable for future policy evolution.
- Adds dedicated Step 77 regression coverage and documentation.

### Step 77 Design Boundary

This step evaluates already-declared provider health only. It does not perform active health probes, network access, credentials, external-provider calls, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 76 Scope

- Adds immutable `RetrievalProviderHealth` identified by provider name.
- Models `healthy`, `unhealthy`, and `unknown` states.
- Preserves stable reasons and explicit health-check state.
- Exposes `is_healthy` for deterministic policy consumption.
- Provides deterministic `to_dict()` serialization.
- Validates provider identity, state, reason, and health-check metadata.
- Keeps health state independent from availability and provider execution.
- Adds dedicated regression coverage for health states, reasons, serialization, immutability, and invalid input.

### Step 76 Design Boundary

This step establishes the provider-health data contract only. It does not perform health checks, network access, credentials, external-provider calls, availability mutation, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

### Step 75 Scope

- Adds immutable `RetrievalProviderAvailabilityEvaluationResult` with explicit available, unavailable, and blocked outcomes.
- Carries availability reason and availability-check state into a stable evaluation result.
- Exposes explicit `supported` and evaluation execution semantics.
- Provides deterministic `to_dict()` serialization.
- Updates `RetrievalProviderAvailabilityEvaluator` to return the result contract instead of a bare boolean.
- Updates `RegistryRetrievalProviderSelector` to consume the explicit availability evaluation result before capability evaluation.
- Updates Step 74 regression coverage for the new evaluator return contract.
- Adds dedicated Step 75 regression coverage for stable states, reasons, serialization, immutability, and invalid combinations.

### Step 75 Design Boundary

This step formalizes availability-evaluation outcomes only. It does not add provider health checks, network access, credentials, external providers, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

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

Steps 54–87 have dedicated regression coverage where documented, but local execution has not been performed in this session. No automated test pass is claimed unless an actual test run reports it.
