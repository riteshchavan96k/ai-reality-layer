# Step 133 — Reality State API Surface

## Objective

Expose the canonical Reality State as a dedicated API surface without invoking model execution.

## Endpoint

`POST /api/v1/reality-state` accepts the existing `SolveRequest` shape (`task`, optional `human_approved` for request compatibility) and returns the canonical Reality State assembled by Step 132.

## Execution boundary

The endpoint uses a dedicated `build_reality_state()` orchestration path. It performs the existing context detection, source planning, retrieval, evidence processing, and Reality State assembly, but does not route to or execute a model and does not run response evaluation/recovery.

The existing `/api/v1/solve` endpoint is unchanged.

## Integration

The API delegates to `build_reality_state()` in the orchestrator. The pipeline method returns the already assembled `state.analysis["reality_state"]` rather than reconstructing it at the HTTP layer.

## Semantic boundary

This endpoint exposes structured reality signals; it is not a truth certificate. No new retrieval provider, LLM, RAG, embeddings, vector database, ML/DL model, or semantic truth judge is introduced.

## Validation

Dedicated regression coverage is in `backend/tests/test_step133.py`. GitHub status checks are not configured. Local pytest execution has not been performed in this session, so no test-pass claim is made.
