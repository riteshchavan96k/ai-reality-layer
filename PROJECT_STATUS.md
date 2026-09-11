# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 56 — Orchestration Composition Boundary — implementation complete; local validation pending.

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

### Step 55 Scope

- Adds a provider-neutral retrieval result contract for reality-information acquisition.
- Gives completed, failed, and blocked retrieval outcomes explicit and deterministic semantics.
- Preserves the original retrieval request across every result state.
- Distinguishes retrieval that actually executed from retrieval that was blocked or not required.
- Converts provider exceptions and malformed provider output into stable failure envelopes without exposing raw exception details.
- Routes `RealityRetrievalEngine` provider output through the stable result boundary before evidence normalization and grounding.
- Adds regression coverage for successful retrieval, provider-unavailable blocking, provider failure, malformed output, and not-required retrieval.

### Step 55 Design Boundary

This step establishes the retrieval execution/result boundary needed before real external reality-information providers are introduced. It does not add external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, or ML training.

### Step 54 Scope

- Routes evaluation-driven quality recovery through the same provider-neutral `ProviderInvocationExecutor` boundary used by primary orchestration execution.
- Resolves provider identity from the normalized model capability catalog before recovery invocation.
- Preserves shared execution-budget accounting across primary execution and quality recovery.
- Preserves retry behavior for provider execution failures during recovery.
- Keeps blocked/non-executed provider results at zero recovery attempts and zero budget consumption.
- Preserves grounded context injection during recovery execution.
- Keeps the legacy adapter-based recovery path available for isolated callers and regression compatibility.
- Adds regression coverage for provider-bound recovery, retry and shared budget behavior, blocked recovery, and unknown provider identity.

### Step 54 Design Boundary

This step unifies quality-recovery execution with the provider invocation/result boundary already used by primary orchestration. It does not add new external providers, API keys, secret storage, credential persistence, external network calls, production provider SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, or ML training.

### Step 53 Scope

- Routes the orchestration execution path through the provider-neutral `ProviderInvocationExecutor` created in Steps 51–52.
- Resolves provider identity from the normalized model capability catalog before provider invocation.
- Preserves the existing ordered fallback and shared execution-budget behavior.
- Preserves retry behavior for provider execution failures while keeping blocked/non-executed results at zero execution attempts.
- Keeps the existing adapter-based fallback path available for isolated callers and regression compatibility.
- Preserves grounded context injection into provider invocation.
- Adds regression coverage for provider-bound execution, failure retry behavior, unknown provider identity, and normal orchestration.

### Step 53 Design Boundary

This step integrates the existing provider invocation and execution-result boundaries into the orchestration execution path. It does not add new external providers, API keys, secret storage, credential persistence, external network calls, production provider SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, or ML training.

### Step 52 Scope

- Added a provider execution result contract after provider invocation execution.
- Successful adapter output is normalized through the existing model response contract instead of exposing provider-specific response shapes downstream.
- Provider execution exceptions are converted into a deterministic failure envelope without exposing raw exception messages or secret-like details.
- Adapter-unavailable invocations remain explicitly blocked with `execution_performed` set to `False`.
- Successful and failed provider attempts explicitly distinguish execution state through `execution_performed`.
- Existing provider credential, readiness, execution gate, invocation, routing, retrieval, grounding, evaluation, recovery, trace, and outcome-memory behavior remains intact.

### Step 52 Design Boundary

This step establishes a stable result boundary between provider invocation and downstream AI Reality Layer processing. It does not add new external providers, API keys, secret storage, credential persistence, external network calls, production retrieval SDKs, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, or ML training.
