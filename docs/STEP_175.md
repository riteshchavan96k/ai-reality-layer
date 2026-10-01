# Step 175 — Request ID Contract Hardening

## Objective

Turn the existing `X-Request-ID` middleware behavior into an explicit, bounded correlation-ID contract that safely preserves valid client IDs, replaces unsafe values, keeps error-body correlation consistent, and documents the header in OpenAPI across public success and failure responses.

## Why this is the correct next step

Step 174 completed the public API error-body contract and made `request_id` part of the safe error envelope.

The next exposed boundary was the correlation identifier itself.

Before Step 175:

- `RequestIdMiddleware` accepted any caller-supplied `X-Request-ID`;
- the value was stored directly in `request.state.request_id`;
- the same unvalidated value was reflected into the response `X-Request-ID` header;
- error handlers could reflect the state value into the JSON body;
- there was no length or character contract;
- the optional request header was not documented in OpenAPI;
- response correlation headers were not documented for 200, 422, or 500 responses.

Step 175 closes that request-correlation integrity boundary.

## Canonical request-ID format

A reusable public request ID must now:

- be a string;
- contain 1–128 characters;
- start with an ASCII letter or digit;
- contain only ASCII letters, digits, `.`, `_`, `:`, and `-` after the first character.

Examples of preserved IDs include:

```
client-123
trace:abc_01
550e8400-e29b-41d4-a716-446655440000
```

Values containing whitespace, control characters, unsupported Unicode, unsupported punctuation, or more than 128 characters are not reflected.

## Safe replacement behavior

Step 175 does not reject the HTTP request merely because its optional correlation ID is malformed.

Instead:

```
missing / invalid X-Request-ID
            ↓
generated UUID4
            ↓
request.state.request_id
            ↓
response X-Request-ID
```

This keeps application availability independent from optional client telemetry while preventing unsafe client-controlled header values from becoming server-reflected identifiers.

## Backward compatibility

Normal identifiers already used by historical tests and likely clients remain valid, including values such as:

```
test-request
request-174
```

The server still accepts requests without `X-Request-ID`.

The only deliberate behavioral change is that unsafe or oversized client identifiers are replaced instead of echoed.

## Middleware integration

`backend/app/api/request_id.py` now exposes:

- `REQUEST_ID_HEADER`;
- `REQUEST_ID_MAX_LENGTH`;
- `is_valid_request_id()`;
- `canonical_request_id()`;
- OpenAPI request-parameter metadata;
- OpenAPI response-header metadata; and
- the existing `RequestIdMiddleware`.

The middleware stores exactly the same canonical ID that it emits in the response header.

This preserves one correlation identity for the complete request lifecycle.

## Error-body integration

Step 174 error handlers now trust a request-state ID only when it satisfies the Step 175 request-ID contract.

If a handler is invoked with malformed or externally corrupted state, the unsafe value is not reflected into the error JSON.

In normal application execution, middleware has already established a valid canonical ID before the handler runs.

## OpenAPI request header

All three public routes now document the optional:

`X-Request-ID`

request header:

- `GET /health`;
- `POST /api/v1/solve`;
- `POST /api/v1/reality-state`.

The schema documents the 1–128 character bound and safe character pattern.

The description states that missing or invalid values are replaced with a generated UUID.

## OpenAPI response header

The canonical response header is documented on the actual response statuses currently exposed by each public route.

### GET /health

- 200;
- 500.

### POST /api/v1/solve

- 200;
- 422;
- 500.

### POST /api/v1/reality-state

- 200;
- 422;
- 500.

This makes request correlation discoverable to API clients on successful responses and documented failure responses.

## Response-body schema preservation

Adding `200` response-header metadata does not replace the response body contracts established by previous steps.

The solve 200 response remains:

`SolveResponse`.

The Reality State 200 response remains:

`RealityStateResponse`.

Likewise, Step 174's 422 and 500 error schemas remain:

- `ValidationErrorResponse`;
- `InternalErrorResponse`.

Step 175 adds header metadata around those contracts rather than redefining them.

## Safety invariant

optional client correlation ID
→ bounded validation
→ preserve safe value or generate UUID
→ one canonical request-state ID
→ error-body correlation where applicable
→ response `X-Request-ID` header
→ documented API client contract.

A request ID is an opaque correlation token only. It does not authenticate a caller, authorize a request, identify a user, establish tenancy, or provide a security boundary.

## Design boundary

Step 175 is request-correlation contract hardening only.

It does not change:

- authentication or authorization;
- orchestration;
- retrieval;
- grounding;
- routing;
- model/provider execution;
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

`backend/tests/test_step175.py` covers:

1. valid request-ID preservation;
2. maximum-length boundary preservation;
3. generated UUID replacement for missing/empty/unsafe/oversized values;
4. middleware state/header identity for valid client IDs;
5. middleware replacement consistency for unsafe IDs;
6. invalid request-state ID non-reflection by error handlers;
7. request-header OpenAPI documentation on every public route;
8. response-header documentation on all applicable 200/422/500 statuses;
9. preservation of solve and Reality State 200 response body schemas;
10. preservation of Step 174 422/500 response body schemas; and
11. absence of an unnecessary health 422 response.

## Validation truth

Dedicated Step 175 regression coverage is committed. Repository structure and the final Git diff are verified in this workflow. The available runtime reports Pydantic 2.13.4 and FastAPI 0.128.2. A targeted pytest run covering Steps 175, 174, 24, and 173 was attempted from a fresh checkout, but the runtime could not resolve `github.com`; the clone failed before pytest started. No automated test-pass claim is made.
