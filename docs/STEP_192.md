# Step 192 — Canonical Freshness Count Type Integrity

## Objective

Harden the canonical source-freshness result so every count field is a true
non-negative integer rather than merely a value that compares equal to one.

Step 159 established count consistency for `SourceFreshnessResult`. Later
steps hardened the numeric measurements, timestamps, classifications, and
unknown-policy semantics. A Python runtime type loophole remained in the
aggregate count boundary.

## Verified gap

Before Step 192:

- `source_count=True` could pass when one assessment existed because
  `bool` is a subclass of `int`;
- `fresh_count=True` could compare equal to computed count `1`;
- `stale_count=False` and `unknown_count=False` could compare equal to
  computed count `0`;
- equal-valued floats such as `fresh_count=1.0` could pass the tuple
  equality check even though the canonical contract declares integer counts.

This matters because the canonical freshness object is serialized into the
Reality State and its stale/unknown aggregate counts are consumed by
confidence aggregation.

## Safety invariant

canonical freshness assessments
→ strict integer aggregate counts
→ count/state consistency
→ confidence signals
→ Reality State

The canonical result now requires all of the following to be:

- instances of `int`;
- explicitly not `bool`;
- non-negative.

The protected fields are:

- `source_count`
- `fresh_count`
- `stale_count`
- `unknown_count`

Only after their type/range validity is established are they compared against
the assessment collection and derived fresh/stale/unknown state totals.

## Implementation

`SourceFreshnessResult.__post_init__()` now:

1. validates `source_count` as a strict non-negative integer excluding
   booleans;
2. validates each aggregate freshness count with the same strict rule;
3. verifies `source_count == len(assessments)`;
4. derives the actual fresh/stale/unknown totals from the typed assessments;
5. verifies the declared aggregate counts match those derived totals;
6. preserves the existing execution/status/reason consistency rules.

No coercion is performed. Values such as `1.0`, `"1"`, `True`, and
`False` are rejected rather than silently normalized.

## Mapping/deserialization integrity

`SourceFreshnessResult.validate()` reconstructs mapping-shaped results and
then enters the same canonical `__post_init__` boundary.

Therefore JSON/Python mappings cannot bypass the rule by using booleans or
equal-valued floats for count fields.

## Compatibility

All normal production outputs remain unchanged because
`SourceFreshnessResult.usable_result()`, `empty_result()`, and
`unavailable_result()` already generate real Python integer counts.

Step 192 does not change:

- Step 186 finite age/window rules;
- Step 189 canonical timestamp rules;
- Step 190 fresh/stale inequality rules;
- Step 191 unknown-policy-window semantics;
- evaluator classification thresholds;
- confidence aggregation policy;
- provenance, claims, conflicts, API inputs, or retrieval behavior.

## Regression coverage

`backend/tests/test_step192.py` covers:

- rejection of boolean `source_count`;
- rejection of non-integer source-count types;
- rejection of boolean, float, and string aggregate counts;
- rejection of negative aggregate integer counts;
- mapping/deserialization rejection of boolean and float loopholes;
- acceptance of legitimate integer counts across fresh/stale/unknown mixtures;
- preservation of empty/unavailable zero counts;
- preservation of Step 190 classification integrity;
- preservation of Step 191 unknown-policy integrity;
- compatibility with downstream confidence aggregation.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation commit on `main`,
and the final synchronized `main` status commit.

## Deliberate non-goals

Step 192 does not broaden count hardening into unrelated historical result
contracts. Those contracts should only be changed when a concrete downstream
need or separately identified step justifies it.

It also does not introduce publication-time inference, source-authenticity
verification, factual-truth scoring, new providers, persistence,
authentication, UI, monitoring, model/LLM judging, or autonomous behavior.
