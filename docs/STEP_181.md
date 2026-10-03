# Step 181 — Explicit Source Observation Freshness Policy

## Objective

Allow developers using the direct-evidence Reality State endpoint to provide an explicit source observation timestamp and an explicit freshness window, so AI Reality Layer can distinguish fresh, stale, and unknown source evidence without treating ingestion time as publication time.

## Why this is the correct next step

Step 180 made developer-supplied evidence a first-class MVP input.

That path intentionally left freshness as unknown because the system only knew when the submitted evidence entered AI Reality Layer. Ingestion time is not proof of when the developer's retrieval/search/RAG system observed the source, and it is not proof of when the source was published.

Freshness is one of the core product differentiators in the product vision. The next useful capability is therefore not another internal contract, but an explicit source-time and freshness-policy input that can drive the existing canonical freshness evaluator.

Step 181 adds that capability without guessing or silently inventing source timestamps.

## New direct-evidence fields

Each direct evidence document may now include:

`observed_at`

Example:

```json
{
  "title": "Company X official update",
  "uri": "https://example.com/company-x",
  "content": "Company X launched Feature A.",
  "observed_at": "2026-10-03T12:30:00Z"
}
```

The request may additionally include:

`freshness_max_age_seconds`

Example:

```json
{
  "task": "What is the current status of Company X?",
  "freshness_max_age_seconds": 3600,
  "documents": [...]
}
```

## Observation semantics

`observed_at` means:

> the time the caller's own retrieval/search/RAG/connector system observed or obtained this source.

It does **not** mean:

- publication time;
- event occurrence time;
- source truth time;
- independent verification time.

AI Reality Layer treats it as caller-supplied observation metadata.

The source URI remains provenance identity only. The direct-evidence endpoint does not fetch the URI to verify the timestamp.

## Canonical observation provenance

The source observation contract now recognizes three explicit methods:

- `retrieval_observation` — AI Reality Layer observed the source through its retrieval pipeline;
- `submitted_evidence_observation` — the caller supplied an explicit `observed_at`;
- `submitted_evidence_ingestion` — the caller supplied no observation time, so the metadata records when AI Reality Layer ingested the submitted document.

This prevents direct-evidence ingestion from being mislabeled as retrieval observation.

## Freshness policy is explicit

Step 181 never classifies a submitted source as fresh merely because an `observed_at` exists.

A freshness assessment requires both:

1. an explicit observation timestamp for every document; and
2. an explicit positive `freshness_max_age_seconds`.

If the freshness window is absent:

```
observed_at supplied
→ observation metadata preserved
→ freshness = unknown
```

If a freshness window is supplied but any document lacks `observed_at`, the request fails validation.

This prevents a missing source timestamp from silently inheriting ingestion time and receiving a misleading fresh/stale classification.

## Timestamp validation

Submitted `observed_at` values must:

- be valid ISO-8601 timestamps;
- include a timezone;
- not be in the future.

They are normalized to UTC with a `Z` suffix.

Examples accepted:

```
2026-10-03T12:30:00Z
2026-10-03T18:00:00+05:30
```

A timezone-naive value such as:

```
2026-10-03T12:30:00
```

is rejected.

## Freshness window validation

`freshness_max_age_seconds` must be a positive integer or float.

The API explicitly rejects:

- zero;
- negative numbers;
- booleans;
- numeric strings.

This avoids Pydantic-style coercion turning `true` into an unintended one-second freshness window.

## Canonical freshness evaluation

Step 181 reuses the existing `SourceFreshnessEvaluator`.

No parallel freshness algorithm is introduced.

For each source:

```
age = evaluator current time - observed_at
```

If:

```
age <= freshness_max_age_seconds
```

the source is:

`fresh`

otherwise it is:

`stale`.

Without a declared window, the source remains:

`unknown`

with reason:

`freshness_window_not_declared`.

## Confidence behavior

The existing conservative confidence rules remain intact.

### All sources known fresh

When:

- evidence quality is usable;
- all claims have evidence links;
- there are no detected conflicts;
- all source freshness assessments are fresh;

the Reality State may be:

`supported`.

### At least one stale source

A stale source produces:

`stale_sources_present`

and the confidence state remains:

`uncertain`.

### No freshness window

Unknown freshness produces:

`freshness_uncertain`

and the confidence state remains:

`uncertain`.

Step 181 therefore makes the supported/uncertain distinction depend on explicit freshness evidence rather than ingestion recency.

## Domain/API defense in depth

The freshness policy is validated in both:

- the Pydantic HTTP request contract; and
- the submitted-evidence domain bundle.

Therefore direct Python callers cannot bypass the rule that an explicit freshness window requires `observed_at` for every submitted document.

## Existing compatibility

Step 180 requests remain valid.

A developer may still submit:

```json
{
  "task": "What is the current status of Company X?",
  "documents": [
    {
      "uri": "https://example.com/source",
      "content": "Company X launched Feature A."
    }
  ]
}
```

That path records submission ingestion metadata and keeps freshness unknown.

The original task-only retrieval endpoint is unchanged.

## Design boundary

Step 181 adds explicit observation-age freshness for developer-supplied evidence.

It does not add:

- publication-time extraction;
- webpage fetching;
- source timestamp verification;
- semantic source trust;
- vendor search;
- learned freshness models;
- calibrated probabilities;
- authentication/authorization;
- persistence;
- vector databases;
- embeddings;
- model training;
- autonomous agents.

## Regression coverage

`backend/tests/test_step181.py` covers:

1. valid observation timestamps and freshness windows;
2. UTC timestamp normalization;
3. naive timestamp rejection;
4. future timestamp rejection;
5. malformed timestamp rejection;
6. zero/negative/boolean/string freshness-window rejection;
7. request-level all-source observation requirement;
8. domain-level all-source observation requirement;
9. canonical submitted-observation methods;
10. explicit observation metadata construction;
11. ingestion observation metadata when timestamp is absent;
12. all-fresh evidence producing supported confidence when other signals permit;
13. stale evidence forcing uncertain confidence;
14. observation timestamp without a window remaining unknown;
15. HTTP handler forwarding the freshness policy;
16. OpenAPI exposure of `observed_at` and `freshness_max_age_seconds`.

## Validation truth

Backend tests run #92 (`37128168903`) on the initial Step 181 regression-bearing commit passed the complete backend suite with **1210 passed / 0 failed**.

Final Step 181 completion requires documentation and project-status synchronization to reproduce a fully green GitHub-hosted suite on the exact final HEAD.
