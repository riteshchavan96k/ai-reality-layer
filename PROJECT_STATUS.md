# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 39 — Retrieval Evidence Normalization — implementation and validation coverage complete.

### Step 39 Scope

- Retrieval results are normalized into a stable evidence structure.
- Source provenance is preserved through normalized title and URI fields.
- Source counts and content presence are explicit.
- Provider failure and non-required retrieval states are preserved.
- Completed retrieval with no usable evidence is marked `invalid_evidence`.
- Invalid provider output shapes are rejected rather than silently accepted.
- Normalized evidence is attached to task analysis before model execution.
- Required retrieval cannot proceed to model execution when usable evidence is unavailable.
- Existing approval, execution, evaluation, recovery, budget, trace, and outcome-memory behavior remains intact.

### Step 39 Design Boundary

This step establishes a stable evidence representation between retrieval and downstream reasoning. It does not verify factual correctness, rank source quality, implement RAG, perform citation grounding, add production web providers, or introduce ML training. Those capabilities can consume the normalized evidence contract in later steps.
