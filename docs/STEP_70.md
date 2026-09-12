# Step 70 — Retrieval Provider Capability Selection Boundary

## Objective

Connect the Step 69 capability contract to provider selection without coupling selection to provider-specific execution logic.

## Implementation

Added `RetrievalProviderDescriptor` to keep provider name, implementation, and declared capabilities together as stable selection metadata.

Extended `RetrievalProviderRegistry` to:

- register providers with capability descriptors
- retrieve provider descriptors independently from provider implementations
- preserve existing provider registration behavior

Updated `RegistryRetrievalProviderSelector` to:

- validate the request through `RetrievalProviderRequest` when capability metadata is present
- accept a provider only when its declared source type and temporal scope support the request
- return a stable unavailable selection with `retrieval_provider_capability_mismatch` when the provider is not capable
- preserve legacy provider registration behavior when no descriptor is supplied

## Design boundary

This step establishes capability-aware provider selection. It does not execute providers, add external retrieval services, or introduce network access. It does not add API keys, secret storage, credential persistence, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, ML training, or LLM integration.

## Validation truth

Dedicated regression coverage is included in `backend/tests/test_step70.py`.

Local execution remains pending until the development environment is available.

Recommended command:

```powershell
python -m unittest backend.tests.test_step70 -v
```

Optional full suite:

```powershell
python -m unittest discover -s backend/tests -p "test*.py" -v
```
