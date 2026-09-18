# Step 134 — Reality State API Contract Hardening

## Objective

Harden the Step 133 Reality State API boundary so its HTTP request and response schemas explicitly represent the Reality State interface instead of reusing the broader solve request contract.

## Scope

- Adds a dedicated `RealityStateRequest` containing only the `task` field.
- Rejects unsupported request fields such as the solve-only `human_approved` field.
- Adds a typed `RealityStateResponse` describing the canonical Step 132 Reality State shape.
- Declares the response model on `POST /api/v1/reality-state`, making the contract visible to FastAPI/OpenAPI clients.
- Preserves the dedicated execution-free Reality State construction path from Step 133.
- Preserves `POST /api/v1/solve` unchanged.
- Hardens the unavailable fallback so it still conforms to the canonical response shape.

## Boundary

This step is API-contract hardening only. It does not add a retrieval provider, network access, credentials, LLM, RAG, embeddings, vector database, semantic truth judgment, ML/DL model, or model execution.

The endpoint still represents structured evidence-backed signals rather than a truth certificate or calibrated probability.

## Regression Coverage

`backend/tests/test_step134.py` covers:

- dedicated request-field boundary;
- rejection of solve-only request fields;
- task length validation;
- canonical response-field shape;
- response status validation;
- route request/response model wiring.

## Validation Truth

GitHub status checks are not configured. Local pytest execution was not performed in this session, so no test-pass claim is made.
