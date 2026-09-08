# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 40 — Evidence Quality and Provenance Validation — implementation complete; local validation pending.

### Step 40 Scope

- Normalized retrieval evidence is structurally validated before downstream model execution.
- Evidence usability requires completed retrieval, usable content, at least one source, and complete provenance.
- HTTP and HTTPS source URIs are validated when a URI is provided.
- Title-only sources remain valid provenance when no URI is available.
- Evidence quality issues are returned explicitly instead of being silently ignored.
- Required retrieval is blocked when evidence quality is insufficient.
- Non-required retrieval remains non-blocking.
- Existing retrieval normalization, approval, execution, evaluation, recovery, budget, trace, and outcome-memory behavior remains intact.

### Step 40 Design Boundary

This step establishes structural evidence-quality and provenance validation between retrieval and downstream reasoning. It does not verify factual correctness, rank source quality, implement RAG, add production web providers, perform citation-grounded generation, or introduce ML training. Those capabilities can consume the validated evidence contract in later steps.
