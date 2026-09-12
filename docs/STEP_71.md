# Step 71 — Retrieval Provider Capability Evaluation Contract

## Objective

Separate provider capability evaluation from provider selection so capability-fit logic can evolve independently from registry lookup and selection orchestration.

## Implementation

Added `RetrievalProviderCapabilityEvaluator` as a dedicated boundary for evaluating a typed `RetrievalProviderRequest` against `RetrievalProviderCapabilities`.

Updated `RegistryRetrievalProviderSelector` to delegate capability matching to the evaluator while preserving existing registry lookup, typed request validation, stable selection results, capability mismatch semantics, and legacy providers without descriptors.

## Design boundary

This step isolates capability-fit evaluation only. It does not execute providers, add external retrieval services, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

## Validation truth

Dedicated regression coverage is included in `backend/tests/test_step71.py`.

Local execution remains pending until the development environment is available.

Recommended command:

```powershell
python -m unittest backend.tests.test_step71 -v
```

Optional full suite:

```powershell
python -m unittest discover -s backend/tests -p "test*.py" -v
```
