# Step 74 — Retrieval Provider Availability Evaluation

## Objective

Separate retrieval-provider availability evaluation from provider selection, mirroring the capability-evaluation boundary established in earlier retrieval architecture work.

## Implementation

- Added `RetrievalProviderAvailabilityEvaluator`.
- The evaluator accepts only the typed `RetrievalProviderAvailability` contract.
- `available` evaluates to eligible for selection.
- `unavailable` and `blocked` evaluate to ineligible.
- Invalid evaluator input is rejected deterministically.
- `RegistryRetrievalProviderSelector` now delegates availability decisions to the evaluator before capability evaluation.
- The selector preserves the existing stable unavailable result and reason semantics.
- The evaluator is injectable, allowing future availability policy to evolve without coupling it to registry lookup or selection orchestration.

## Design Boundary

This step evaluates already-declared availability state. It does not perform network health checks, provider probing, retries, credentials, external provider integration, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

## Validation

Dedicated regression tests cover available, unavailable, blocked, invalid input, selector delegation, and selection short-circuit behavior.

Local test execution remains pending unless an actual local or CI run reports success.
