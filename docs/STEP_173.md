# Step 173 — Solve API Contract Hardening

## Objective

Give `POST /api/v1/solve` dedicated HTTP request and response contracts backed by the canonical Step 172 orchestration-result boundary, without changing the endpoint's existing runtime semantics or sparse terminal response shapes.

## Why this is the correct next step

Step 172 established a canonical runtime contract for every terminal orchestration result and enforced it at the pipeline and public `orchestrate_task()` boundaries.

The next exposed boundary was the HTTP layer.

Before Step 173:

- `/api/v1/solve` used an inline `SolveRequest` declared in `main.py`;
- unknown request fields were not explicitly forbidden;
- the route had no FastAPI `response_model`;
- OpenAPI therefore did not document a dedicated solve response schema;
- FastAPI did not independently validate/serialize the outgoing solve response against an HTTP response contract.

The neighboring `/api/v1/reality-state` endpoint had already received dedicated request/response models in Step 134. Step 173 applies the same API-hardening principle to the solve surface, while reusing Step 172 instead of inventing a competing orchestration schema.

## Dedicated HTTP module

Step 173 adds:

`backend/app/api/solve.py`

with:

- `SolveRequest`;
- `SolveResponse`; and
- `SolveStatus`.

## SolveRequest

The request contract preserves the existing fields:

- `task`: 1–10,000 characters;
- `human_approved`: boolean, default `False`.

It now uses:

`ConfigDict(extra="forbid")`

so unsupported request properties fail validation rather than being silently ignored.

## Backward compatibility

Historical Step 24 tests and callers import:

`SolveRequest` from `backend.app.main`.

Step 173 preserves that import path because `main.py` imports the dedicated class into its module namespace.

No caller migration is required.

## SolveResponse

The response contract declares the six terminal statuses defined by Step 172:

- `awaiting_human_approval`;
- `retrieval_unavailable`;
- `grounding_unavailable`;
- `execution_context_unavailable`;
- `execution_failed`;
- `orchestrated`.

Common fields are required:

- `analysis`;
- `routing`;
- `approval`;
- `trace`.

Status-specific fields remain optional at the Pydantic surface because the Step 172 canonical validator is responsible for exact per-status requirements.

This avoids duplicating orchestration invariants inside the HTTP schema.

## Canonical response validation

`SolveResponse` uses a Pydantic before-validator that routes the raw response through:

`OrchestrationResultNormalizer`.

Therefore HTTP response validation reuses the exact Step 172 runtime contract for:

- terminal status validation;
- status-specific required fields;
- execution summary integrity;
- trace integrity;
- grounding;
- evaluation;
- recovery;
- outcome memory; and
- cross-object consistency.

The HTTP layer does not maintain a second independent version of those rules.

## Extension metadata

The response uses:

`ConfigDict(extra="allow")`

so valid future extension metadata preserved by Step 172 is not stripped from the HTTP response.

## Sparse response compatibility

Blocked/failure terminal responses historically omit fields that do not apply.

Step 173 configures the solve route with:

`response_model_exclude_unset=True`.

This prevents optional response-model defaults from adding unrelated `null` fields such as execution/result/evaluation to an approval-blocked response.

Existing sparse dictionary semantics are preserved.

## FastAPI route hardening

The solve route now declares:

- request body model: `SolveRequest`;
- response model: `SolveResponse`;
- unset response-field exclusion.

As a result, OpenAPI now documents named solve request and response schemas.

## Safety invariant

canonical orchestration result
→ dedicated SolveResponse validation
→ FastAPI response serialization
→ `POST /api/v1/solve` client.

The HTTP contract validates structure and consistency. It does not establish factual truth, semantic correctness, grounding completeness, safety for every downstream use, or calibrated model quality.

## Design boundary

Step 173 is API-contract hardening only.

It does not change:

- orchestration control flow;
- approval policy;
- retrieval;
- evidence processing;
- grounding;
- model routing;
- provider execution;
- retry/fallback;
- evaluation;
- recovery;
- outcome memory;
- Reality State generation;
- credentials;
- external network behavior;
- RAG;
- embeddings;
- ML/DL training; or
- semantic truth inference.

## Regression coverage

`backend/tests/test_step173.py` covers:

1. dedicated request-contract placement with legacy import compatibility;
2. rejection of unknown solve request fields;
3. bounded task validation;
4. route request/response contract declaration;
5. exhaustive solve status schema;
6. sparse blocked-response preservation;
7. extension metadata preservation;
8. reuse of Step 172 trace validation;
9. unknown terminal-status rejection;
10. status-specific missing-field rejection;
11. OpenAPI request/response schema exposure; and
12. required common response fields.

## Validation truth

Dedicated Step 173 regression coverage is committed. Repository structure and the final Git diff are verified in this workflow. The available runtime has compatible Pydantic 2.x and FastAPI versions, and a targeted pytest run covering Steps 173, 172, 134, and 24 was attempted from a fresh checkout. The runtime could not resolve `github.com`, so the clone failed before pytest started. No automated test-pass claim is made.
