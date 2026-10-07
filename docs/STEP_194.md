# Step 194 — Canonical Source-Observation Execution-State Integrity

## Objective

Ensure a canonical source-observation result cannot expose usable observations
while simultaneously claiming that source observation did not execute.

Step 158 introduced the canonical `SourceObservationResult` contract and
included `observation_executed` as part of that result. The field was validated
as a boolean, but its semantic relationship to a `usable` result was not
enforced.

## Verified gap

Before Step 194, this canonical shape was accepted:

```text
status = "usable"
observations = [valid source observation]
source_count = 1
observation_executed = False
```

That state is internally contradictory: it exposes completed source-observation
records while declaring that source observation did not execute.

The contradiction matters downstream because `SourceFreshnessEvaluator`
consumes the observation status and observation collection. It does not use
`observation_executed` when deciding whether to evaluate freshness. A
mapping-shaped observation result could therefore deny execution while still
producing usable freshness that later contributes to confidence.

## Safety invariant

source provenance
→ source observation
→ canonical source-observation result
→ freshness
→ confidence
→ Reality State

If the canonical source-observation result is `usable`, then source
observation must be recorded as executed:

```text
status == "usable"
→ observation_executed is True
```

This prevents contradictory execution metadata from entering the downstream
freshness stage.

## Implementation

`SourceObservationResult.__post_init__()` now enforces:

- `observation_executed` must remain a boolean;
- when `status == "usable"`, `observation_executed` must be `True`.

Existing validation remains intact for:

- canonical nested `SourceObservation` values;
- source-count/collection consistency;
- usable/empty/unavailable observation shape;
- unavailable reasons;
- Step-189 timestamp validation and UTC normalization.

## Why empty and unavailable are not over-constrained

Step 194 deliberately does **not** force
`observation_executed=True` for `empty` or `unavailable` results.

Those statuses do not contain usable source observations and therefore cannot
legitimately produce a positive downstream freshness signal. They may also
represent a pipeline where source observation was skipped or unavailable.

The existing production helpers and builders currently emit
`observation_executed=True` for their normal empty/unavailable outputs, and
Step 194 preserves that behavior while leaving the canonical contract capable
of representing an explicitly non-executed empty/unavailable state.

## Mapping/deserialization integrity

`SourceObservationResult.validate()` reconstructs mapping-shaped inputs through
the canonical result constructor.

`SourceFreshnessEvaluator` also reconstructs mapping-shaped observation
inputs as `SourceObservationResult` before freshness evaluation.

Therefore a mapping cannot bypass Step 194 by supplying
`status="usable"` with `observation_executed=False`.

## Compatibility

Normal production behavior is unchanged.

`SourceObservationResult.usable_result()` already uses the default
`observation_executed=True`, and both source-observation builder paths create
usable results only after actual observation construction.

Step 194 preserves:

- Step 188 shared timestamp bounds;
- Step 189 canonical observation timestamps;
- Step 190 fresh/stale classification integrity;
- Step 191 unknown freshness policy integrity;
- Step 192 strict freshness count types;
- Step 193 usable freshness execution-state integrity;
- existing freshness/confidence semantics;
- provenance, claims, conflicts, APIs, retrieval behavior, and resource limits.

## Regression coverage

`backend/tests/test_step194.py` covers:

- direct rejection of usable observations with `observation_executed=False`;
- mapping/deserialization rejection;
- normalizer rejection;
- acceptance of usable observations with execution `True`;
- rejection of non-boolean execution values;
- deliberate acceptance of explicit non-executed empty/unavailable results;
- preservation of current helper semantics;
- downstream freshness rejection of contradictory observation mappings;
- downstream acceptance of valid executed observation mappings;
- source-observation builder integration;
- retrieval-observation builder integration;
- Step-189 timestamp canonicalization non-regression;
- Step-193 downstream freshness execution integrity non-regression.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation commit on `main`,
and the final synchronized `main` status commit.

## Deliberate non-goals

Step 194 does not broaden execution-state hardening into source provenance or
other historical result contracts. Those boundaries should be changed only
when their own downstream contradiction is separately verified.

It also does not add publication-time inference, source-authenticity
verification, factual-truth scoring, new providers, persistence,
authentication, UI, monitoring, model/LLM judging, or autonomous behavior.
