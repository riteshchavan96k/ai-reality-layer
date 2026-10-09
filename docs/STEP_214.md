# Step 214 — Per-Source Observation and Freshness Integrity

## Verified correctness gap after Step 213

Step 213 established that one canonical `SourceProvenanceResult` cannot
contain repeated source IDs or references. Downstream temporal records,
however, remained independently constructible and deserializable:

- `SourceObservationResult` checked `source_count == len(observations)`,
  but allowed multiple observations with the **same source_id** within one
  result, even with different timestamps or observation methods.
- `SourceFreshnessResult` validated its `fresh_count`, `stale_count`
  and `unknown_count` against the number of assessment records, but it
  did not require those records to represent **different sources**.
  One source could therefore appear as both fresh and stale in a single
  canonical freshness result, with superficially consistent counts.

The ordinary pipeline emits one record per source, but direct typed
construction, mapping deserialization and subsequent consumers can
otherwise reintroduce this ambiguity. Those source counts feed
Reality State freshness signals, so repeated records must not masquerade
as independent evidence.

## Objective

Enforce **one observation and one freshness assessment per source ID
within each result**, in both canonical typed contracts and
mapping-based validation, while retaining all historical valid outputs.

## Changes

Only two existing production contracts were changed:

- `backend/app/reality/source_observation.py`: in
  `SourceObservationResult.__post_init__`, reject repeated
  `item.source_id` values using
  `ValueError("source observation source_ids must be unique")`.
- `backend/app/reality/source_freshness.py`: in
  `SourceFreshnessResult.__post_init__`, reject repeated
  `item.source_id` values using
  `ValueError("source freshness source_ids must be unique")`.

Checks are performed **after** the existing type and source-count
validation, so they operate only on validated typed record tuples.

Existing `validate(mapping)` and the pre-existing normalizers
construct those canonical result types and thereby enforce the same
invariants without introducing an additional service or helper.

The normal `SourceObservationBuilder` produces one observation for
each unique provenance source from Step 213, and
`SourceFreshnessEvaluator` produces one assessment for each validated
observation. Neither needs a new API or algorithm change.

## Behavioral examples

| Input | Result |
| --- | --- |
| One observation for source A | Valid |
| One observation each for A and B | Valid |
| Two observations for A, same timestamp | Rejected |
| Two observations for A, different method/timestamp | Rejected |
| One freshness assessment each for A and B | Valid |
| Fresh and stale assessments both assigned to A | Rejected |
| Repeated identical fresh assessments for A | Rejected |
| Separate fresh, stale, unknown assessments for A, B, C | Valid, exact counts |
| Empty/unavailable canonical result | Valid as before |

**This is within-one-result identity integrity, not a temporal history
store.** The same source may legitimately have many observations at
different times in different Reality State snapshots; this step does
not prohibit or model that future temporal functionality.

## Regression and downstream coverage

`backend/tests/test_step214.py` covers:

1. Typed observation duplicates, including different methods.
2. Explicit typed observation constructor with duplicate IDs.
3. Mapping and normalizer rejection of duplicated observations.
4. Freshness duplicates with identical and contradictory states.
5. Explicit freshness constructor with superficially consistent counts.
6. Mapping and normalizer rejection of duplicated assessments.
7. A downstream freshness evaluator refusing duplicate observation
   mappings **before computing source counts**.
8. Distinct-source typed/mapping round trips and correct freshness counts.
9. Mixed distinct-source fresh/stale/unknown count preservation.
10. Provenance-to-observation-to-freshness processing for two distinct
    sources.
11. Existing empty, unavailable and unknown-state behavior.
12. A real developer-submitted Reality State preserving two separate
    provenance, observation and freshness records and source-scoped
    claim attribution.

Complete historical Python 3.13 backend compilation and pytest
regression suite is required, including Steps 158–159, 189–195
and 212–213.

## Strict boundaries

- One canonical observation per source **within a snapshot**; no
  persistence or historical event aggregation is added.
- Source ID values, SHA-256 URI identity, timestamp parsing, observation
  methods, freshness age policy and confidence aggregation remain unchanged.
- No change to public APIs, request/response shape, retrieval providers,
  dependency graph or database.
- No ML, DL, Hugging Face, LLM, semantic inference, knowledge graph, or
  independent source credibility/factual truth determination.
- Passing a source cardinality check does **not** establish that the
  source is authentic or that its underlying evidence is true.

## Completion standard

Only mark complete after full GitHub-hosted Python 3.13 compile and
pytest succeed on the PR head, PR is merged into `main`, merged-main
CI succeeds, and a final repository status update succeeds on its
exact `main` commit.
