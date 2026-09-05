# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 36 — Reality Source Planning — implementation and validation coverage complete.

### Step 36 Scope

- Reality-context requirements are converted into a deterministic source plan.
- Current-information tasks are assigned a live-web source requirement.
- Explicit external-evidence tasks are assigned a web-or-official-source requirement.
- Static tasks retain model knowledge as the default source type without requiring retrieval.
- Temporal scope is preserved in the source plan.
- The source plan is attached to task analysis for downstream retrieval components.
- Existing execution, evaluation, recovery, budget, approval, trace, and outcome-memory behavior remains intact.

### Step 36 Design Boundary

This step plans what kind of source is required; it does not fetch external information, call the web, implement RAG, normalize evidence, verify factual correctness, or introduce ML training. Those capabilities can consume this source-plan contract in later steps.
