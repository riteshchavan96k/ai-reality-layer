# Step 99 — Grounding Execution Context Contract

## Objective

Create a canonical execution-context boundary between the Reality Layer grounding pipeline and model execution.

The grounding gate in Step 97 determines whether execution may proceed, and Step 98 guarantees that this gate decision is canonical. Step 99 now converts the already-normalized grounding representation into a dedicated execution context so model execution no longer consumes the generic grounding state directly.

## Implementation

- Added `GroundingExecutionContext` as an immutable dataclass.
- Preserves the original task, grounded content, source metadata, source count, and grounding status.
- Carries the execution permission established by the grounding gate.
- Validates source-count consistency and rejects evidence attached to `not_available` contexts.
- Added `from_grounding()` for conversion from the normalized grounding mapping.
- Added explicit `ready_result()` and `not_available_result()` constructors.
- Added deterministic serialization through `to_dict()`.
- Extended `OrchestrationState` with `execution_context`.
- Updated the orchestration pipeline to create the execution context only after the normalized grounding gate allows execution.
- Updated model execution and recovery to consume the dedicated execution context instead of the raw grounding mapping.
- Added a trace event for execution-context preparation.
- Added dedicated regression coverage for valid contexts, unavailable contexts, source consistency, execution permission, invalid status, invalid types, and deterministic serialization.

## Architectural Boundary

`grounding context contract → grounding context normalization → grounding context consumption → grounding context consumption result → grounding context consumption normalization → grounding execution gate → grounding execution gate normalization → grounding execution context → execution`

This is an important separation: the Reality Layer establishes and validates the world representation first, then creates the exact context that downstream model execution is permitted to consume.

## Scope Discipline

Step 99 does not add an LLM provider, RAG framework, embeddings, vector database, model training, or external retrieval API. It establishes the execution-facing contract that those future intelligence components can consume without coupling them directly to the grounding pipeline's internal state.

## Validation Truth

Dedicated regression tests are included. Local test execution has not been performed in this session, so no local test pass is claimed.
