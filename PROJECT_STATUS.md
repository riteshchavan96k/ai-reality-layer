# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 41 — Evidence Grounding Context and Model Injection — implementation complete; local validation pending.

### Step 41 Scope

- Validated retrieval evidence is converted into a stable grounding context before model execution.
- Grounding context preserves retrieved content and normalized source provenance.
- Usable evidence becomes a `ready` grounding context; insufficient or unavailable evidence becomes `not_available`.
- The model adapter contract accepts optional execution context without requiring every future provider to implement retrieval-specific behavior immediately.
- The fallback executor and evaluation-guided recovery preserve the same grounding context across model attempts.
- The mock model records grounding metadata so the execution boundary can be tested without a real external provider.
- Required retrieval remains blocked before model execution when evidence quality is insufficient.
- Non-required retrieval remains non-blocking and passes an explicit `not_available` grounding state.
- Existing routing, approval, retry, fallback, evaluation, recovery, trace, and outcome-memory behavior remains intact.

### Step 41 Design Boundary

This step establishes the evidence-to-model grounding contract and context-injection boundary. It does not implement a production web provider, full RAG pipeline, embedding/vector search, source ranking, factual verification, citation generation, model training, or learned grounding. Those capabilities can consume the grounding context in later steps.
