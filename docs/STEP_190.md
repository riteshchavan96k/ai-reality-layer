# Step 190 — Canonical Freshness Classification Integrity

## Objective

Make the canonical source-freshness contract prove that its declared
`fresh`/`stale` classification agrees with the finite observation age and
finite freshness window it carries.

Steps 159, 186, and 189 progressively hardened the same contract:

- Step 159 established canonical `SourceFreshnessAssessment` and
  `SourceFreshnessResult` validation.
- Step 186 required finite, nonnegative `age_seconds` and positive finite
  `max_age_seconds`.
- Step 189 made `observed_at` canonical and bounded across typed and
  mapping-shaped freshness records.

After Step 189, one semantic invariant was still missing: the typed freshness
assessment accepted a status whose own numeric fields contradicted that status.

## Verified gap

Before Step 190, all of the following were structurally valid canonical
assessments:

- `status="fresh", age_seconds=61, max_age_seconds=60`
- `status="stale", age_seconds=59, max_age_seconds=60`
- `status="stale", age_seconds=60, max_age_seconds=60`

The production `SourceFreshnessEvaluator` itself does not generate these
combinations: it classifies a source as fresh when
`age_seconds <= max_age_seconds` and stale only when the age is strictly
greater. But direct typed construction and
`SourceFreshnessResult.validate()` mapping deserialization could create the
contradictory states.

Because downstream confidence consumes the resulting freshness status/counts,
a canonical freshness object must not claim a classification that disagrees
with its own finite measurements.

## Safety invariant

canonical observation timestamp
→ finite nonnegative observation age
→ positive finite declared window
→ classification derived consistently from those values
→ canonical source freshness result
→ deterministic confidence signals / Reality State

For classified assessments:

- `fresh` requires `age_seconds <= max_age_seconds`
- `stale` requires `age_seconds > max_age_seconds`

The exact boundary remains fresh, matching the existing evaluator.

## Implementation

`SourceFreshnessAssessment.__post_init__()` now validates the relationship
between the already-required finite age/window values and the declared status.

The existing validation sequence remains intact:

1. source identity is nonblank;
2. status is one of `fresh`, `stale`, or `unknown`;
3. Step 189 canonicalizes and validates `observed_at`;
4. Step 186 validates finite numeric age/window values;
5. fresh/stale assessments require both values;
6. **Step 190 validates classification consistency**;
7. unknown/reason and assessment-method rules remain unchanged.

No duplicate evaluator or new classification algorithm is introduced. The
canonical contract now enforces the same inequality already used by
`SourceFreshnessEvaluator`.

## Mapping/deserialization integrity

`SourceFreshnessResult.validate()` reconstructs nested mappings as typed
`SourceFreshnessAssessment` values. Therefore the new invariant also applies
to deserialized freshness results automatically.

A mapping cannot bypass the rule by supplying internally consistent aggregate
counts around an individually contradictory assessment.

## Compatibility

All outputs produced by the existing `SourceFreshnessEvaluator` remain valid.

Specifically:

- age exactly equal to the declared window remains `fresh`;
- age strictly greater than the window remains `stale`;
- unknown freshness remains reason-based and is not given a new policy;
- Step 186 finite-number rules remain unchanged;
- Step 189 timestamp normalization remains unchanged;
- fresh/stale/unknown aggregate counting remains unchanged.

This is a fail-closed canonical-contract hardening change for malformed direct
or mapping-shaped inputs, not a change to normal production classification.

## Regression coverage

`backend/tests/test_step190.py` covers:

- rejection of fresh assessments older than their declared window;
- rejection of stale assessments still inside the declared window;
- rejection of stale status at the exact boundary;
- acceptance of fresh status at the exact boundary;
- acceptance of stale status strictly beyond the boundary;
- mapping/deserialization rejection of contradictory fresh/stale records;
- mapping acceptance of consistent fresh/stale records;
- preservation of unknown-freshness semantics;
- evaluator behavior exactly at and just beyond the declared boundary;
- non-regression of Step 186 finite-number enforcement;
- non-regression of Step 189 canonical timestamp enforcement.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation on `main`, and
the final synchronized `main` status commit.

## Deliberate non-goals

Step 190 does not:

- change freshness thresholds or introduce a default freshness window;
- infer publication time or event occurrence time;
- verify source authenticity or factual truth;
- change confidence aggregation policy;
- add a provider, database, authentication, UI, monitoring, model, LLM judge,
  or autonomous action.

Freshness remains an observation-age classification under an explicitly
declared policy, not a truth certificate or calibrated probability.
