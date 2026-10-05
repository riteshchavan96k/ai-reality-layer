# Step 188 — Consistent, Bounded Source-Observation Timestamp Validation

## Verified MVP gap

The AI Reality Layer MVP uses explicit observation timestamps for age-based
freshness analysis, but does **not** treat observation age as publication time,
source authenticity or verified factual truth. Step 181 added reported
timestamps to developer-submitted evidence; Steps 183–184 established a
64-character `observed_at` bound on retrieved evidence; Steps 186–187
protected finite windows and made submitted evidence source-scoped.

Inspecting the final Step 187 `main` implementation revealed a real
contract disparity: `EvidenceDocumentInput.observed_at` was an *unbounded*
optional string and `SubmittedEvidenceDocument.__post_init__` passed
unbounded user input to an independent `datetime.fromisoformat` parser.
The canonical `SourceObservation` itself could also accept an unbounded
timestamp. Retrieved evidence used a different, already bounded provider
field. Long invalid strings could therefore reach direct-evidence parsing
and/or canonical observation objects despite bounded source content.

The original high-level MVP specification never assigned a particular
Step 188 title; this step is identified by that **existing, verified
observation-metadata trust-boundary gap**, not an invented new feature.

## Solution

A single source-neutral constant
`MAX_SOURCE_OBSERVED_AT_CHARS = 64` now establishes the **maximum raw**
`observed_at` character count for *both* source paths.

1. **Canonical timestamp parser:** `normalize_reported_observation_time`
   validates input type, checks raw length **before stripping or parsing**,
   rejects empty or malformed ISO-8601, requires a timezone, rejects
   timestamps in the future, normalizes offsets to UTC `Z` and strips
   outer whitespace. The method describes when the caller/provider
   **reports observing** a source, not a verified publication date.
2. **Direct-evidence API:** `EvidenceDocumentInput.observed_at` declares
   `max_length=64`, including OpenAPI schema metadata, and delegates
   the date/time validation to the shared parser.
3. **Direct-evidence domain:** `SubmittedEvidenceDocument` delegates to
   the same parser. Python callers that bypass HTTP cannot pass
   overlength, invalid, timezone-naive or future observations.
4. **Retrieved evidence:** Existing
   `MAX_RETRIEVED_OBSERVED_AT_CHARS` remains exported for backwards
   compatibility but now aliases the same shared 64-character constant.
   The HTTP/provider-neutral and evidence-normalizer boundaries retain
   their previous fail-closed behavior and reasons.
5. **Canonical observation records:** `SourceObservation` now enforces
   the same raw timestamp length bound. A typed or dictionary-converted
   record cannot reintroduce unbounded date metadata.

## Exact boundary and compatibility

- A nonblank, timezone-aware ISO-8601 timestamp with **exactly** 64 raw
  characters (including ignorable outer whitespace) is accepted and
  normalized; 65 or more raw characters are rejected. The bound is
  measured **before** normalization to prevent large whitespace or
  overly precise timestamps bypassing the limit.
- Existing normalized `observed_at` values such as
  `2026-01-01T12:30:00Z` or
  `2026-01-01T18:00:00+05:30` retain their previous meaning and
  normalize to the same UTC instant.
- Missing `observed_at` with no freshness window remains valid; the
  source-observation method distinguishes ingestion from an explicit
  source observation. Missing timestamps do **not** meet explicit
  developer-requested freshness windows.
- Stale evidence remains stale for the declared finite policy. No
  processing timestamps are substituted to upgrade reported-source
  freshness. Original source identity, claims, per-source content and
  link/conflict logic remain unchanged.
- Direct-evidence requests with timestamp strings longer than 64
  characters now return validation errors instead of parsing them.
  This is an intentional hardening change. Existing values within the
  length bound retain API and internal behavior.

## Implementation files

- `backend/app/reality/source_observation.py`: single source-neutral
  timestamp limit and early raw input check in canonical parsing
  and typed observations.
- `backend/app/reality/retrieval_input_bounds.py`: reuse shared
  constant without removing its established retrieval-specific name.
- `backend/app/reality/submitted_evidence.py`: reuse canonical
  timezone/UTC parser rather than separately parsing timestamps.
- `backend/app/api/evidence_reality_state.py`: Pydantic length
  constraint and shared timestamp parser.
- `backend/tests/test_step188.py`: direct/API/retrieval/typed schema
  boundary regressions and end-to-end freshness/source integrity.
- `README.md` and `PROJECT_STATUS.md`: document the changed
  request metadata contract and completion evidence.

## Verification criteria

- Positive and negative cases at 64/65 characters, including a very long
  malformed input, are tested on API and Python/domain boundaries.
- Configured retrieval, provider-neutral validation, normalizer, and
  canonical observation mapping remain consistently bounded.
- Timezone-naive, invalid, future and blank timestamps remain rejected.
- Existing in-bounds offset-to-UTC normalization and freshness/provenance
  semantics are unchanged, including no-policy unknown freshness.
- The complete existing backend suite must pass in GitHub CI after PR
  merge and on the final synchronized `main` HEAD. A passing
  standalone test file is not sufficient for completion.

## Non-goals

No fetched publisher verification, semantic factual truth guarantee,
network provider, model or LLM, autonomous action, persistent storage,
authentication changes, UI/dashboard or production load-testing.
Source-observation time is declarative metadata only.
