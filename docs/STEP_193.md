# Step 193 — Canonical Freshness Execution-State Integrity

## Objective

Ensure a canonical source-freshness result cannot contain usable freshness
assessments while simultaneously claiming that freshness evaluation did not
execute.

Step 159 introduced the canonical `SourceFreshnessResult` contract and
included `freshness_executed` as part of that result. The field was validated
as a boolean, but its semantic relationship to a `usable` result was not
enforced.

## Verified gap

Before Step 193, this canonical shape was accepted:

```text
status = "usable"
assessments = [fresh assessment]
fresh_count = 1
freshness_executed = False
```

That state is contradictory: it exposes completed freshness assessments while
also declaring that freshness evaluation did not execute.

The contradiction matters downstream because confidence aggregation consumes
the freshness status and aggregate counts, not `freshness_executed`. A
mapping-shaped canonical freshness result could therefore carry a positive
freshness signal while its execution metadata denied that the evaluation ran.

## Safety invariant

source observations
→ freshness evaluation
→ canonical freshness result
→ confidence signals
→ Reality State

If the canonical freshness result is `usable`, then freshness evaluation must
be recorded as executed:

```text
status == "usable"
→ freshness_executed is True
```

This guarantees that usable freshness assessments and their execution metadata
cannot contradict one another.

## Implementation

`SourceFreshnessResult.__post_init__()` now enforces:

- `freshness_executed` must still be a boolean;
- when `status == "usable"`, `freshness_executed` must be `True`.

The existing validation remains intact for:

- strict Step-192 count types;
- source-count/assessment-count consistency;
- fresh/stale/unknown aggregate consistency;
- usable/empty/unavailable assessment shape;
- unavailable reasons.

## Why empty and unavailable are not over-constrained

Step 193 deliberately does **not** require
`freshness_executed=True` for `empty` or `unavailable` results.

Those statuses cannot contribute a positive freshness signal to confidence.
They may also legitimately describe a pipeline where freshness processing was
skipped or could not run.

The existing production helpers and `SourceFreshnessEvaluator` currently emit
`freshness_executed=True` for their empty and unavailable outputs, and Step
193 preserves that behavior. It simply leaves the canonical contract flexible
enough to represent an explicit non-executed empty/unavailable state.

## Mapping/deserialization integrity

`SourceFreshnessResult.validate()` reconstructs mapping-shaped inputs through
the canonical result constructor.

Therefore mappings cannot bypass Step 193 by supplying
`status="usable"` with `freshness_executed=False`.

## Compatibility

Normal production behavior is unchanged.

`SourceFreshnessResult.usable_result()` already uses the default
`freshness_executed=True`, and `SourceFreshnessEvaluator` produces usable
results only after running its freshness logic.

Step 193 also preserves:

- Step 186 finite numeric measurement rules;
- Step 189 canonical observation timestamps;
- Step 190 fresh/stale classification consistency;
- Step 191 unknown-policy integrity;
- Step 192 strict count-type integrity;
- existing empty/unavailable evaluator behavior;
- downstream confidence policy.

## Regression coverage

`backend/tests/test_step193.py` covers:

- direct rejection of usable results with `freshness_executed=False`;
- mapping/deserialization rejection;
- normalizer rejection;
- preservation of usable results with execution `True`;
- rejection of non-boolean execution values;
- deliberate acceptance of explicitly non-executed empty/unavailable states;
- preservation of existing helper/evaluator execution semantics;
- confidence compatibility for valid executed freshness;
- non-regression of Steps 191 and 192.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation commit on `main`,
and the final synchronized `main` status commit.

## Deliberate non-goals

Step 193 does not broaden execution-state hardening into every older result
contract. Other boundaries should be changed only when their own concrete
downstream inconsistency is separately verified.

It also does not add publication-time inference, source-authenticity
verification, factual-truth scoring, new providers, persistence,
authentication, UI, monitoring, model/LLM judging, or autonomous behavior.
