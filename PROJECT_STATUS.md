# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 37 — Reality Retrieval Contract — implementation and validation coverage complete.

### Step 37 Scope

- A structured retrieval request contract is created from the Step 36 source plan.
- Retrieval requests preserve the original task as the retrieval query.
- Source type and temporal scope are carried forward for downstream retrieval providers.
- Required versus not-required retrieval is explicit.
- The contract reports that retrieval has not yet been executed.
- The retrieval contract is attached to task analysis for future retrieval implementations.
- Existing execution, evaluation, recovery, budget, approval, trace, and outcome-memory behavior remains intact.

### Step 37 Design Boundary

This step defines the interface between source planning and future retrieval execution. It does not fetch external information, call the web, implement RAG, normalize or verify evidence, claim factual correctness, or introduce ML training. Future retrieval providers can consume this contract without changing the orchestration architecture.
