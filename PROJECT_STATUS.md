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

### Step 72 Scope

- Adds immutable `RetrievalProviderCapabilityEvaluationResult` with explicit supported/unsupported states.
- Carries source type, temporal scope, support state, reason, and evaluation execution state.
- Provides deterministic serialization through `to_dict()`.
- Updates `RetrievalProviderCapabilityEvaluator` to return the result contract instead of a bare boolean.
- Updates `RegistryRetrievalProviderSelector` to consume the explicit evaluation result while preserving capability-mismatch semantics.
- Adds dedicated regression coverage for supported/unsupported results, serialization, and immutability.

### Step 71 Scope

- Adds a dedicated `RetrievalProviderCapabilityEvaluator` for provider/request capability-fit evaluation.
- Separates capability evaluation from registry lookup and provider-selection orchestration.
- Updates `RegistryRetrievalProviderSelector` to delegate capability matching to the evaluator.
- Preserves typed `RetrievalProviderRequest` validation before capability evaluation.
- Preserves stable `retrieval_provider_capability_mismatch` selection semantics.
- Preserves legacy provider registration and selection when no capability descriptor is present.
- Adds regression coverage for compatible requests, source/temporal mismatches, and invalid inputs.

### Step 70 Scope

- Adds immutable `RetrievalProviderDescriptor` metadata combining provider identity, implementation, and declared capabilities.
- Extends `RetrievalProviderRegistry` with descriptor registration and lookup while preserving legacy registration.
- Updates provider selection to use declared capabilities.
- Converts selection mappings into typed `RetrievalProviderRequest` before capability matching.
- Blocks capability-incompatible requests with stable mismatch semantics without executing providers.
- Preserves legacy providers without descriptors.
- Adds Step 70 regression coverage and documentation.

### Steps 69–56

Steps 69–56 established the typed retrieval capability, provider, response/result normalization, selection/registry, and orchestration composition boundaries documented in prior project history.

## Validation Truth

Steps 54–74 have dedicated regression coverage where documented, but local execution has not been performed in this session. No automated test pass is claimed unless an actual test run reports it.
