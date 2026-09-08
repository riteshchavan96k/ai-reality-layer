# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 45 — Provider Adapter Boundary — implementation complete; local validation pending.

### Step 45 Scope

- A provider-level adapter contract now separates provider identity from model selection and model capability metadata.
- Providers expose a stable identity and a factory boundary for constructing model adapters.
- The current internal mock model is represented through the same provider boundary used by future providers.
- Model adapter lookup now resolves the normalized model capability profile first, then delegates construction to its declared provider.
- Unknown models and unknown providers fail cleanly at the registry boundary.
- Existing response normalization, routing, approval, retrieval, evidence validation, grounding, evaluation, recovery, trace, and outcome-memory behavior remains intact.

### Step 45 Design Boundary

This step establishes the provider integration interface without integrating any external production provider. It does not add API credentials, external network calls, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, or ML training.
