# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 58 — Orchestration State Contract — implementation complete; local validation pending.

### Step 58 Scope

- Adds an explicit `OrchestrationState` contract for state carried across pipeline stages.
- Replaces positional stage-state coordination in `OrchestrationPipeline.run` with named state fields.
- Centralizes task, analysis, routing, approval, retrieval, evidence, grounding, execution, evaluation, recovery, and outcome state.
- Provides named accessors for the retrieval contract and final execution result.
- Preserves the existing public orchestration result shape and functional pipeline behavior.
- Preserves Step 56 dependency injection and Step 57 stage boundaries.
- Adds regression coverage for state defaults, named state access, and pipeline result compatibility.

### Step 58 Design Boundary

This step reduces internal state-coupling between orchestration stages and establishes a stable state contract for future pipeline evolution. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production provider SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, or ML training.

### Step 57 Scope

- Adds an explicit `OrchestrationPipeline` boundary around the existing orchestration sequence.
- Decomposes the large orchestration function into explicit preparation/approval, retrieval/grounding, execution, and evaluation/recovery stages.
- Keeps the public `orchestrate_task` entry point stable while delegating pipeline execution to the new boundary.
- Preserves dependency injection introduced in Step 56.
- Preserves the shared execution budget across primary execution and quality recovery.
- Preserves existing routing, retrieval, grounding, evaluation, recovery, trace, outcome-memory, fallback, and approval semantics.
- Adds regression coverage for stage execution, shared budget propagation, and approval blocking before retrieval.

### Step 57 Design Boundary

This step reduces procedural coupling in the orchestration entry point without changing the pipeline's functional behavior. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production provider SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, or ML training.

### Step 56 Scope

- Adds an explicit `OrchestrationDependencies` composition boundary for services used by the orchestration pipeline.
- Centralizes construction of the default orchestration service graph in one dependency-composition object.
- Allows `orchestrate_task` callers to inject service implementations without changing the existing pipeline behavior.
- Removes direct construction of retrieval, evidence, grounding, approval, and provider-execution services from the orchestration function body.
- Preserves the existing optional `approval_policy` and `retrieval_engine` injection points for backward compatibility.
- Adds regression coverage for the default dependency graph and injected-service orchestration behavior.
- Does not redesign the pipeline sequence or change existing execution, retrieval, grounding, evaluation, recovery, trace, or outcome-memory semantics.

### Step 56 Design Boundary

This step establishes dependency composition and injection needed before further orchestration decomposition. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production provider SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, latency optimization, or ML training.
