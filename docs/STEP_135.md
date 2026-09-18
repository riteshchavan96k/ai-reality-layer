# Step 135 — External Retrieval Provider Adapter

## Objective

Introduce the first real external-information acquisition adapter behind the existing provider-neutral retrieval boundary, without coupling the Reality Layer to a specific search vendor.

## Implementation

- Adds `HttpRetrievalProvider` as an opt-in HTTPS provider adapter.
- Accepts the existing typed `RetrievalProviderRequest`.
- Expands `{query}` into a URL-encoded query in a configured HTTPS endpoint template.
- Expects a JSON object with optional `content` and `sources` fields.
- Converts the external response into the existing `RetrievalProviderResponse` contract.
- Adds a source record from the request URL when content is returned without explicit sources.
- Enforces a request timeout and maximum response size.
- Fails closed on network errors, invalid JSON, invalid payload shape, and oversized responses.

## Configuration

The adapter is disabled by default. Set `ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE` to an HTTPS URL template containing `{query}` to opt in. When configured, the default dependency graph registers the provider for `live_web` and `web_or_official_source` source types.

No endpoint, credentials, or secret is hardcoded into the repository.

## Boundary

The adapter provides transport and response normalization only. It does not decide whether retrieved information is true, does not perform semantic claim verification, and does not add LLM/RAG/embeddings/vector search/ML/DL. The existing Reality State pipeline remains responsible for evidence normalization, provenance, freshness, conflict signals, and state assembly.

## Safety / Reliability

- HTTPS is required.
- Query text is URL-encoded.
- Response size is bounded.
- Timeout is bounded.
- External failures become a failed provider response instead of being treated as evidence.
- The provider remains opt-in so existing deployments do not unexpectedly begin making network requests.

## Regression Coverage

`backend/tests/test_step135.py` covers HTTPS/template validation, query encoding, JSON normalization, source fallback, invalid payload handling, response-size limits, typed request enforcement, and opt-in/default dependency registration.

## Validation Truth

GitHub status checks are not configured. Local pytest execution was not performed in this session, so no test-pass claim is made.
