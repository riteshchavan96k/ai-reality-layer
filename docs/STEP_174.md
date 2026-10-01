# Step 174 — API Error Contract Hardening

## Objective

Add canonical, safe HTTP error contracts for request-validation failures and unexpected server failures, route the existing FastAPI exception handlers through those contracts, and document the real 422/500 response shapes in OpenAPI.

## Why this is the correct next step

Step 173 completed the success-side HTTP contract for `POST /api/v1/solve`.

The next exposed boundary was the shared error surface.

Before Step 174:

- request-validation failures returned a custom JSON dictionary from `validation_exception_handler()`;
- unexpected failures returned a second custom JSON dictionary from `unhandled_exception_handler()`;
- neither error shape had a canonical Pydantic model;
- the custom 422 response differed from FastAPI's default OpenAPI validation-error schema;
- 500 responses were not explicitly documented on the public routes;
- raw Pydantic validation details included rejected `input` values and validator `ctx` metadata, which were forwarded directly to clients.

That left the API with typed success responses but an untyped and potentially over-disclosing failure surface.

Step 174 closes that boundary.

## Canonical error models

Step 174 adds:

`backend/app/api/error_contract.py`

with exact status-specific contracts.

### ValidationErrorResponse

The 422 envelope is:

```
{
  "status": "error",
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [...]
  },
  "request_id": "..."
}
```

The error code and message are literals matching the existing API behavior.

### InternalErrorResponse

The 500 envelope is:

```
{
  "status": "error",
  "error": {
    "code": "internal_error",
    "message": "An internal server error occurred."
  },
  "request_id": "..."
}
```

The internal-error contract has no details field.

This deliberately prevents an exception object or internal diagnostic from becoming part of the public 500 schema.

## Safe validation details

Public validation issues expose only:

- `type`;
- `loc`;
- `msg`.

Step 174 deliberately strips:

- rejected `input` values; and
- raw validator `ctx` metadata.

This is a data-minimization boundary.

A malformed request can contain secrets, tokens, large payloads, or other sensitive values. Those values are useful for local debugging but do not need to be reflected back by the public error API.

Raw validator context can also contain custom exception objects or implementation details, so it is omitted from the public contract.

## Handler integration

`backend/app/api/errors.py` now constructs error responses through:

- `build_validation_error_response()`; and
- `build_internal_error_response()`.

Both handlers serialize validated Pydantic models rather than assembling ad-hoc dictionaries.

The 500 handler explicitly discards the supplied exception object before response construction.

## Request ID compatibility

The existing top-level `request_id` field is preserved.

If middleware supplies an ID, it is returned unchanged.

If the handler is invoked without a usable request ID, the key is still emitted with `null`, matching the historical envelope shape rather than silently removing the field.

## OpenAPI integration

The application now explicitly declares canonical error models.

### POST /api/v1/solve

Documents:

- 200: `SolveResponse`;
- 422: `ValidationErrorResponse`;
- 500: `InternalErrorResponse`.

### POST /api/v1/reality-state

Documents:

- 200: `RealityStateResponse`;
- 422: `ValidationErrorResponse`;
- 500: `InternalErrorResponse`.

### GET /health

Documents:

- 200: existing health response;
- 500: `InternalErrorResponse`.

The health endpoint does not advertise a request-validation 422 because it has no request body contract requiring that response.

## Exact schemas instead of one broad error union

Step 174 uses separate 422 and 500 response classes rather than one model that allows either error code.

This makes OpenAPI precise:

- a 422 response is documented specifically as `validation_error`;
- a 500 response is documented specifically as `internal_error`.

## Compatibility

Step 174 preserves:

- HTTP status codes;
- top-level `status="error"`;
- existing error codes;
- existing public error messages;
- top-level request IDs;
- existing global FastAPI exception-handler registration.

The deliberate hardening change is validation-detail minimization: rejected input values and raw validator context are no longer reflected to clients.

## Safety invariant

request/handler failure
→ canonical status-specific error contract
→ sensitive-detail minimization
→ request-ID correlation
→ JSON serialization
→ documented public HTTP response.

A canonical API error describes the API failure safely. It does not expose internal exception details, credentials, rejected secret values, stack traces, or private debugging state.

## Design boundary

Step 174 is API error-contract and disclosure hardening only.

It does not change:

- orchestration;
- model execution;
- retrieval;
- grounding;
- routing;
- provider behavior;
- retry/fallback;
- response evaluation;
- quality recovery;
- outcome memory;
- Reality State logic;
- credentials;
- external provider configuration;
- RAG;
- embeddings;
- ML/DL training; or
- semantic truth inference.

## Regression coverage

`backend/tests/test_step174.py` covers:

1. exact canonical 422 construction;
2. rejected-input removal;
3. raw validator-context removal;
4. canonical validation-handler output;
5. request-ID preservation;
6. legacy null request-ID field preservation;
7. exact safe 500 construction;
8. exception-message non-disclosure;
9. solve endpoint 422/500 OpenAPI models;
10. Reality State endpoint 422/500 OpenAPI models;
11. health endpoint 500 documentation without an unnecessary 422;
12. OpenAPI validation-detail field minimization; and
13. rejection of unknown fields by canonical error models.

## Validation truth

Dedicated Step 174 regression coverage is committed. Repository structure and the final Git diff are verified in this workflow. Runtime test execution is reported separately and is never inferred from committed tests.
