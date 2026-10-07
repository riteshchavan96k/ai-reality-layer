# Step 191 — Canonical Unknown-Freshness Policy Integrity

## Objective

Complete the semantic integrity of canonical source-freshness assessments by
ensuring that an assessment declared as `unknown` cannot simultaneously carry
an explicit freshness policy window.

The current MVP freshness contract has a deliberate three-way meaning:

- `fresh`: an explicit freshness window exists and the measured observation age
  is inside or exactly on that window;
- `stale`: an explicit freshness window exists and the measured observation age
  is strictly beyond that window;
- `unknown`: no freshness window was declared, so the system refuses to infer a
  freshness classification.

Steps 181 and 183 introduced that explicit-policy rule for submitted and
retrieved evidence. Steps 159, 186, 189, and 190 progressively hardened the
canonical freshness structure, finite numeric values, timestamps, and
fresh/stale classification consistency.

After Step 190, one contradictory canonical state remained possible:
`status="unknown"` together with a non-null `max_age_seconds`.

## Verified gap

Before Step 191, the canonical contract accepted values such as:

```text
status = "unknown"
max_age_seconds = 3600
reason = "freshness_window_not_declared"
```

This is internally contradictory: the record says no freshness policy was
declared while also carrying an explicit 3600-second policy window.

The same contradiction could be created through
`SourceFreshnessResult.validate()` mapping reconstruction.

The normal production `SourceFreshnessEvaluator` does not generate this shape.
When no window is supplied it emits `unknown` with
`freshness_window_not_declared`; when a window is supplied it emits
`fresh` or `stale`. Canonical validation must enforce that same semantic
boundary for direct typed and mapping-shaped construction.

## Safety invariant

source observation
→ optional explicit freshness policy
→ canonical source-freshness assessment

If a policy window exists:
→ classify `fresh` or `stale`

If no policy window exists:
→ `unknown`

A canonical `unknown` assessment therefore requires:

`max_age_seconds is None`

This prevents contradictory policy metadata from reaching confidence
aggregation or the Reality State.

## Implementation

`SourceFreshnessAssessment.__post_init__()` now rejects any `unknown`
assessment whose `max_age_seconds` is non-null.

The validation remains layered:

1. source identity validation;
2. status validation;
3. Step 189 canonical `observed_at` validation;
4. Step 186 finite age/window validation;
5. required measurements for fresh/stale;
6. Step 190 fresh/stale inequality consistency;
7. **Step 191 unknown/policy-window consistency**;
8. unknown-reason and assessment-method validation.

No parallel freshness evaluator or new state is introduced.

## Deliberate age behavior

Step 191 does **not** require `age_seconds` to be null for an `unknown`
assessment.

A source observation age can be measurable even when no classification policy
window exists. The semantically decisive field is `max_age_seconds`, because
that field represents the explicit policy needed to classify the observation.

This preserves future compatibility for callers that may retain a finite
measured age while correctly refusing to classify it without a policy.

## Mapping/deserialization integrity

`SourceFreshnessResult.validate()` constructs nested
`SourceFreshnessAssessment` objects.

Therefore mapping-shaped inputs inherit the same invariant automatically.
A mapping cannot bypass Step 191 by supplying consistent aggregate counts while
embedding an `unknown` assessment with a policy window.

## Compatibility

Normal production behavior is unchanged:

- no declared window → `unknown`;
- declared window + usable observation → `fresh` or `stale`;
- exact window boundary remains `fresh` from Step 190;
- declared window without required usable observation metadata follows the
  existing unavailable/fail-closed path from Steps 181 and 183;
- finite numeric protections from Step 186 remain;
- canonical timestamp protections from Step 189 remain;
- confidence remains uncertain for unknown freshness.

## Regression coverage

`backend/tests/test_step191.py` covers:

- direct rejection of `unknown` with a declared policy window;
- rejection with or without a measured age;
- mapping and normalizer rejection of the contradictory state;
- valid unknown state with no policy window;
- preservation of an optional finite age with no policy window;
- preservation of the required unknown reason;
- evaluator output without a window;
- evaluator output with a declared window;
- downstream confidence remaining uncertain for unknown freshness;
- non-regression of Step 190 fresh/stale classification;
- non-regression of Step 186 finite age validation;
- non-regression of Step 189 timestamp validation.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, on the merged implementation commit in
`main`, and on the final synchronized `main` status commit.

## Deliberate non-goals

Step 191 does not:

- infer publication time or event time;
- introduce a default freshness window;
- change freshness thresholds;
- change confidence aggregation policy;
- establish source authenticity or factual truth;
- add a provider, persistence layer, authentication, UI/dashboard, monitoring,
  LLM/model judge, or autonomous behavior.

Freshness remains an explicit observation-age policy signal, not a truth
certificate or calibrated probability.
