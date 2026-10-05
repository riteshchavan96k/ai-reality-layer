# Step 183 — Explicit Retrieved-Source Observation Freshness Policy

## Objective

Extend the configured retrieval → Reality State path with provider-reported
per-source observation timestamps and an optional developer-declared freshness
window. The source timestamps are **claims by the retrieval provider about
when it observed the source**, not inferred publication dates, verified source
ownership, event dates, or factual-truth certificates.

## Why this follows Steps 180–182

- Step 180 accepts source-scoped developer evidence.
- Step 181 permits explicit observed_at and freshness_max_age_seconds on
  the direct-evidence API without treating ingestion as freshness.
- Step 182 corrects configured retrieval's per-source claim attribution.

Before Step 183, the configured retrieval path assigned each retrieved
source the current pipeline time, marked retrieval_observation, and evaluated
any supplied freshness window against that time. The public retrieval-based
endpoint had no way to request a window at all.

A provider may deliver older cached evidence. The time the Reality Layer
*processes* a provider response does not establish when the provider actually
observed each underlying source. Treating processing time as an explicit
observation under a freshness policy is a trust gap.

## HTTP request contract

Existing endpoint:

    POST /api/v1/reality-state

Request with an optional explicit freshness window:

    {
      "task": "What is the current status of Company X?",
      "freshness_max_age_seconds": 3600
    }

Only a positive, finite integer or float is accepted. Zero, negatives,
booleans, numeric strings, NaN, infinities, and overly large integers are
rejected at the API and domain entry points. The existing task-only request
is still valid. Documents still belong on the separate
/api/v1/reality-state/evidence endpoint, not here.

## Retrieval-provider contract

For source-level observation information, a configured HTTPS retrieval
provider may respond:

    {
      "status": "completed",
      "sources": [
        {
          "uri": "https://example.test/a",
          "content": "Feature A launched.",
          "observed_at": "2026-01-01T12:30:00Z"
        },
        {
          "uri": "https://example.test/b",
          "content": "Feature B launched.",
          "observed_at": "2026-01-01T18:15:00+05:30"
        }
      ]
    }

observed_at is a per-source, timezone-aware, non-future ISO-8601 timestamp.
It is normalized to UTC with a Z suffix. Malformed, naive, non-string,
blank, or future timestamps cause the HTTP retrieval provider to fail closed
with invalid_source_observed_at. Provider-neutral legacy adapter responses
with invalid timestamps become invalid_evidence instead of producing
inaccurate freshness claims.

The already-existing Step 182 source-scoped content and original-URI
requirements remain unchanged. This step does not fetch publisher URIs.

## Observation provenance

SourceObservation now allows:

- retrieval_observation: the Reality Layer's own retrieval processing-time
  observation, retained for legacy provider results **without an explicit
  freshness window**.
- retrieval_provider_observation: a validated **provider-reported** source
  observation timestamp, which is suitable for age evaluation against an
  explicitly requested freshness window but is not independently verified.
- submitted_evidence_observation and submitted_evidence_ingestion: the
  Step 181 direct-evidence methods, unchanged.

These methods must remain distinct. Timestamp ingestion does not imply
publisher verification.

## Safety policy and conservative outcomes

When a developer declares freshness_max_age_seconds:

1. All retrieved source records must include valid provider-reported
   observed_at values.
2. If *any* retrieved source lacks observed_at, the source observation
   contract is unavailable with reason provider_observation_required;
   freshness remains unavailable and confidence cannot be supported.
3. If provider timestamps exist, existing SourceFreshnessEvaluator compares
   source observation age to the window. All within the policy may yield
   supported confidence when evidence, linkage, and conflicts also permit.
4. One stale source forces uncertainty even if others are fresh.
5. No automatic timestamp substitution by the configured retrieval
   endpoint can satisfy a requested freshness policy.
6. If there is no declared freshness window, freshness remains unknown,
   including when provider timestamps are present.

If no explicit policy is declared and no provider timestamps are present,
the existing legacy retrieval_observation metadata is preserved. A developer
must **not** interpret that as verified freshness.

All states reuse the existing provenance, claim, linking, conflicts,
confidence, and Reality State data structures; no model-based source
judgments or external verification are introduced.

## Integration

- backend/app/api/reality_state.py: optional strict request validator
- backend/app/main.py: forwarding request policy
- backend/app/orchestrator/orchestrator.py: typed Python entry point
- backend/app/orchestrator/pipeline.py: policy propagation and conservative
  choice between legacy and provider-source observation processing
- backend/app/reality/http_retrieval_provider.py: validate and preserve
  provider-reported timestamps
- backend/app/reality/evidence_normalizer.py: preserve provider-neutral source
  metadata and fail closed on invalid values
- backend/app/reality/source_observation.py: timestamp validation and
  distinct provider-reported observation method
- backend/app/reality/source_observation_builder.py: source-identity-aligned
  observation building, strict policy requiring all source timestamps
- backend/tests/test_step183.py: complete new regression coverage
- backend/tests/test_step180.py: deliberate compatibility reconciliation
  for the retrieval endpoint's expanded optional policy field

## Regression acceptance criteria

- HTTP API and domain input bounds reject malformed freshness policies.
- Provider timestamps normalize timezone offsets and reject invalid/future.
- Source timestamps remain associated with their original source URI.
- Partial provider timestamps with a policy never imply freshness.
- All-fresh and mixed stale/fresh scenarios reach expected Reality States
  using a deterministic injected clock.
- Provider time without a window does not become fresh.
- Task-only retrieval requests, source-less and unconfigured retrieval,
  direct-submitted evidence from Steps 180–181, and claim lineage from
  Step 182 remain compatible.
- Full hosted CI runs complete backend compilation and the entire pytest
  suite, with no skips to manufacture success.

## Boundaries

No source timestamp authentication, publisher publication-time evaluation,
remote document verification, new provider integrations, semantic truth
checking, model training, embeddings, vector databases, persistence, auth,
deployment, continuous monitoring, or autonomous actions are added.

## Validation truth

The implementation is complete only when the final synchronized GitHub main
commit passes the full backend CI workflow. A green structural test suite
does not prove that any third-party provider is truthful.
