# Step 77 — Retrieval Provider Health Evaluation

## Objective

Separate retrieval-provider health evaluation from the health state contract so health policy can evolve independently from provider selection.

## Implementation

- Added `RetrievalProviderHealthEvaluator`.
- The evaluator accepts only `RetrievalProviderHealth`.
- `healthy` evaluates to `True`.
- `unhealthy` and `unknown` evaluate to `False`.
- Invalid input is rejected deterministically.
- Added explicit health state to `RetrievalProviderRegistry` with a compatibility default of healthy when no explicit state exists.
- Provider replacement clears stale health metadata.
- Updated `RegistryRetrievalProviderSelector` to evaluate health after availability and before capability matching.
- An unhealthy provider is not selected or executed.
- The evaluator remains injectable for future policy evolution.

## Selection Order

The provider-selection boundary now follows:

1. provider lookup
2. availability evaluation
3. health evaluation
4. capability evaluation
5. provider selection

A failed earlier gate short-circuits later policy evaluation.

## Design Boundary

This step evaluates already-declared health state. It does not perform active health probes, network calls, credentials, external-provider calls, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

## Validation Truth

Dedicated regression coverage was added in `backend/tests/test_step77.py` for health evaluation, registry defaults and mutation behavior, selector gating, and invalid input. Local execution remains pending unless an actual test run is performed.
