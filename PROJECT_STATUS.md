# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 46 — Provider Configuration Boundary — implementation complete; local validation pending.

### Step 46 Scope

- A provider configuration contract now separates non-secret provider configuration from provider adapter implementation.
- Provider configuration can declare a provider identity, an optional environment-variable name for credentials, and an optional endpoint without storing credential values.
- The internal provider remains configuration-free because it does not require an external service.
- Provider resolution now requires both a registered provider adapter and a matching provider configuration.
- The model registry continues to resolve models through normalized capability metadata and the declared provider.

### Step 46 Design Boundary

This step establishes the configuration boundary required before production provider integrations. It does not add API keys, secret storage, external network calls, production provider SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, or ML training.
