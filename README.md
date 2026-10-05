# ai-reality-layer
AI Reality Layer — infrastructure for giving autonomous AI systems continuously verified information about the world before they reason, decide, or act.

## Development validation

Install the production and test dependencies through the development requirements file, then run the complete backend regression suite from the repository root:

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest
```

GitHub Actions runs the same backend test suite automatically on pushes and pull requests to `main`.

## MVP current-information retrieval

AI Reality Layer can use an opt-in provider-neutral HTTPS retrieval endpoint for current/external evidence.

Configure an endpoint template containing the literal `{query}` placeholder:

```bash
export ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE='https://retrieval.example.com/search?q={query}'
```

The endpoint must use HTTPS. A successful response should be a JSON object such as:

```json
{
  "status": "completed",
  "content": "Company X launched Feature A today.",
  "sources": [
    {
      "title": "Official Company X update",
      "uri": "https://example.com/company-x"
    }
  ]
}
```

Then call:

```http
POST /api/v1/reality-state
Content-Type: application/json

{
  "task": "What is the current status of Company X?"
}
```

The retrieval service supplies source content only. AI Reality Layer performs the deterministic claims, evidence-linking, provenance, observation, freshness, conflict, confidence-signal, and Reality State assembly stages.

If no retrieval endpoint is configured, requests that require external/current evidence fail closed through the existing unavailable/insufficient Reality State path rather than fabricating evidence.

## Already have search or RAG evidence?

Use the direct evidence endpoint instead of configuring AI Reality Layer retrieval:

```http
POST /api/v1/reality-state/evidence
Content-Type: application/json

{
  "task": "What is the current status of Company X?",
  "documents": [
    {
      "title": "Company X official update",
      "uri": "https://example.com/company-x-official",
      "content": "Company X launched Feature A today."
    },
    {
      "title": "Independent report",
      "uri": "https://example.com/company-x-report",
      "content": "not Company X continues to operate."
    }
  ]
}
```

The documents remain source-scoped during claim extraction, so claims retain the URI(s) they actually came from. Exact duplicate claims across sources are merged while preserving all source references.

This endpoint does not fetch the submitted URIs and does not run the configured retrieval provider. It processes the supplied evidence through evidence-quality validation, claim extraction, claim/evidence linking, provenance, observation, freshness, conflict detection, confidence signals, and Reality State assembly.

Freshness remains uncertain in this initial direct-evidence contract because ingestion time is not treated as source publication time.

## Optional freshness policy for supplied evidence

If your search/RAG/connector already knows when each source was observed, include `observed_at` on every document and declare a freshness window:

```http
POST /api/v1/reality-state/evidence
Content-Type: application/json

{
  "task": "What is the current status of Company X?",
  "freshness_max_age_seconds": 3600,
  "documents": [
    {
      "title": "Company X official update",
      "uri": "https://example.com/company-x",
      "content": "Company X launched Feature A.",
      "observed_at": "2026-10-03T12:30:00Z"
    }
  ]
}
```

`observed_at` means when your system observed the source, not when it was published or independently verified. It must be a timezone-aware ISO-8601 timestamp and cannot be in the future.

When a freshness window is declared, every document must include `observed_at`. Sources inside the declared age window are assessed as fresh; older sources are stale. If no freshness window is supplied, freshness remains unknown even when observation timestamps are present.

If no `observed_at` is supplied, AI Reality Layer records the submission ingestion time for observation metadata but does not use that ingestion time to claim the evidence is fresh.


## Scoped retrieval provenance (Step 182)

For **more than one retrieved source**, the configured HTTPS retrieval service must supply
the text belonging to each original source. A combined text body plus several source
URLs does **not** establish which source supports a claim.

Example of the supported provider-neutral response:

```json
{
  "status": "completed",
  "sources": [
    {
      "uri": "https://example.com/original-a",
      "title": "Original A",
      "content": "Company X launched Feature A. Shared fact."
    },
    {
      "uri": "https://example.com/original-b",
      "title": "Original B",
      "content": "Company X expanded its team. Shared fact."
    }
  ]
}
```

The optional top-level `content` must equal the source documents joined with a
blank line (after trimming each document), if it is supplied. Otherwise the
Reality Layer constructs that combined content itself.

Unique claims are linked only to their contributing original URI, and exactly
duplicate claims merge source references. Multi-source legacy responses without
source-level text do **not** produce misleading claim citations: extraction
becomes unavailable due to ambiguous source attribution. Single-source legacy
responses remain valid.

The retrieval endpoint's own URL is never substituted as the original
publisher's URI if no source is returned. A URI is **caller/provider-supplied
provenance**, not independent verification or proof of factual truth.

See `docs/STEP_182.md` for the full boundary and regression contract.

## Optional freshness policy for configured retrieval (Step 183)

The configured HTTPS retrieval path now supports **provider-reported source
observation times**, separate from the time the Reality Layer processes the
provider response. To declare a freshness requirement, use:

```http
POST /api/v1/reality-state
Content-Type: application/json

{
  "task": "What is the current status of Company X?",
  "freshness_max_age_seconds": 3600
}
```

A source-scoped retrieval response may supply:

```json
{
  "status": "completed",
  "sources": [
    {
      "uri": "https://example.com/original-a",
      "content": "Feature A launched.",
      "observed_at": "2026-01-01T12:30:00Z"
    },
    {
      "uri": "https://example.com/original-b",
      "content": "Feature B launched.",
      "observed_at": "2026-01-01T18:15:00+05:30"
    }
  ]
}
```

`observed_at` means **when the retrieval provider says it observed that
original source**, **not** when the publisher posted it, when the event
occurred, or when AI Reality Layer verified the source. These are
provider-reported times, not independently authenticated statements. All
source timestamps require explicit timezones and cannot be in the future.

When a freshness window is requested, **every source must have a provider-
reported observation timestamp**. Missing timestamps make freshness
unavailable and prevent supported confidence; using the current processing
time as a substitute would misleadingly classify cached evidence as fresh.
Stale sources force uncertainty. Without a declared window, freshness
remains unknown even if observations exist. Legacy single-source and
task-only retrieval requests still work.

See `docs/STEP_183.md` for full rules, compatibility and regression scope.

## Bounded configured retrieval (Step 184)

The configured HTTPS retrieval path now rejects oversized or unexpected
source data **before** extracting claims. These boundaries match the
existing direct-evidence MVP document limits wherever applicable:

- Maximum **20** sources per response.
- Maximum **50,000 characters** of content per original source.
- Maximum **2,048** URI characters and **500** title characters.
- Maximum **64** characters for an optional provider `observed_at` value.
- Maximum **2,000 unique candidate claims** extracted from a retrieved
  response. Inputs exceeding the claim budget produce no partial claims.

The optional `sources[]` fields are `uri`, `title`, `content`, and
`observed_at`. Extra nested metadata is rejected rather than carried
through to the resulting Reality State. Combined text has a bounded
length matching the number of original sources; Step 182's exact aggregate
consistency validation still applies. The HTTPS adapter's existing byte
limit remains in effect.

For invalid retrieved evidence, the system fails closed with a structured
unavailable/insufficient Reality State rather than partially attributing
claims or labeling unsupported evidence as verified. The direct-submitted
evidence API is unchanged.

See `docs/STEP_184.md` for the precise limits and compatibility tests.
