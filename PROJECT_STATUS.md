# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 44 — Model Capability & Provider Contract — implementation complete; local validation pending.

### Step 44 Scope

- Model catalog profiles now have an explicit provider identity.
- A stable capability contract validates model name, provider, and capability metadata before routing uses the profile.
- Duplicate capability declarations are normalized without changing their order.
- Optional model metadata such as context window and grounding support can pass through the contract.
- Model selection consumes normalized capability profiles rather than raw catalog dictionaries.
- Invalid model capability metadata fails early instead of leaking malformed profiles into routing.
- Existing response normalization, routing, approval, retrieval, evidence validation, grounding, evaluation, recovery, trace, and outcome-memory behavior remains intact.

### Step 44 Design Boundary

This step establishes a provider-independent model capability metadata boundary for reliable discovery and routing. It does not add a production model provider, external API credentials, factual verification, semantic evaluation, citation generation, RAG, embeddings/vector search, or ML training.
