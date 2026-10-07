# Step 189 — Canonical Observation/Freshness Timestamp Integrity

## Objective

Complete the Step 188 source-observation timestamp invariant at the canonical
internal-contract layer.

Step 188 established one bounded public/provider timestamp trust boundary:
`normalize_reported_observation_time` accepts at most 64 raw characters,
requires a nonblank timezone-aware ISO-8601 value, rejects future timestamps,
and normalizes accepted values to UTC `Z`.

A final contract gap remained on `main`: canonical `SourceObservation`
objects still maintained a parallel parser, while downstream
`SourceFreshnessAssessment` only required `observed_at` to be a non-empty
string. Direct construction or mapping deserialization could therefore
reintroduce alternate/noncanonical timestamp forms after the external
boundaries had already been hardened.

## Verified gap

The gap is structural and reproducible:

1. `SourceObservation("id", "2026-01-01T18:00:00+05:30")` was valid but
   retained the offset form rather than the canonical
   `2026-01-01T12:30:00Z` representation produced by the Step 188 shared
   validator.
2. `SourceFreshnessAssessment` accepted any non-empty string as
   `observed_at`; its own canonical contract did not independently enforce
   the 64-character bound, ISO-8601 shape, timezone, future-time rule, or UTC
   normalization.
3. `SourceFreshnessResult.validate()` reconstructs nested assessments from
   mappings, so a mapping-shaped canonical freshness result could pass an
   invalid/noncanonical observation timestamp into the typed result contract.

Normal production evaluation usually receives already validated observations,
but canonical contracts must protect their own invariants rather than depend on
one particular upstream path.

## Safety invariant

reported/developer/provider timestamp
→ bounded source-observation normalization
→ canonical `SourceObservation`
→ observation-age evaluation
→ canonical `SourceFreshnessAssessment`
→ canonical `SourceFreshnessResult`
→ confidence / Reality State

Every canonical layer that carries `observed_at` now preserves the same
timestamp representation and validation boundary.

## Implementation

### Canonical source observations

`SourceObservation.__post_init__()` now delegates `observed_at` validation
and normalization to `normalize_reported_observation_time`.

This removes the independent timestamp parser and guarantees that direct typed
construction and `SourceObservationResult.validate()` mapping
deserialization:

- apply the raw 64-character maximum before parsing;
- reject blank, malformed and timezone-naive timestamps;
- reject future timestamps;
- normalize equivalent offsets to UTC `Z`;
- serialize the normalized value.

Existing `observation_method` values and their meaning are unchanged.

### Canonical freshness assessments

`SourceFreshnessAssessment.__post_init__()` now uses the same shared
source-observation normalizer and writes the canonical UTC `Z` value into the
frozen assessment.

Consequently `SourceFreshnessResult.validate()`, which reconstructs nested
typed assessments from mappings, inherits the same timestamp integrity without
introducing a second parser.

Existing Step 186 finite-number checks for `age_seconds` and
`max_age_seconds`, fresh/stale/unknown status rules, assessment method, counts,
and reasons remain unchanged.

## Compatibility

Valid timestamps within the Step 188 boundary remain valid. The only observable
normalization change for callers that directly construct canonical internal
objects is that equivalent timezone-offset/outer-whitespace forms are serialized
in canonical UTC `Z` form.

For example:

`2026-01-01T18:00:00+05:30`

becomes:

`2026-01-01T12:30:00Z`

This matches the behavior already exposed by the submitted-evidence and
retrieved-evidence trust boundaries.

Missing observation timestamps are still handled by the existing upstream
semantics: ingestion observations may be created when appropriate, and an
explicit freshness window still requires explicit source observation metadata
where already specified by Steps 181 and 183.

## Regression coverage

`backend/tests/test_step189.py` covers:

- direct `SourceObservation` UTC-offset normalization;
- source-observation mapping/deserialization normalization;
- exact 64-character and over-limit timestamp boundaries;
- malformed, blank, non-string, timezone-naive, and future observations;
- direct `SourceFreshnessAssessment` normalization;
- freshness-result mapping/deserialization normalization;
- matching invalid/oversized freshness-assessment rejection;
- preservation of unknown-freshness semantics;
- observation-age evaluation and finite freshness policy behavior;
- submitted-evidence → Reality State preservation of one canonical timestamp;
- preservation of the shared Step 188 64-character policy.

The full GitHub-hosted backend compilation and regression suite must pass on
the feature PR and on merged `main`. Passing only the dedicated Step 189 tests
is not sufficient.

## Deliberate non-goals

Step 189 does not introduce publication-time metadata, publisher verification,
source authority scoring, factual-truth guarantees, semantic verification,
new retrieval providers, persistence, authentication, UI/dashboard behavior,
continuous monitoring, model training, LLM judging, or autonomous action.

`observed_at` remains declarative source-observation metadata. It is not a
verified publication date or proof that a claim is true.
