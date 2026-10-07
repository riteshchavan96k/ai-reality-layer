# Step 195 — Canonical Source-Provenance Execution-State Integrity

## Objective

Ensure a canonical source-provenance result cannot expose usable source
identities while simultaneously claiming that provenance assignment did not
execute.

Step 157 introduced the canonical `SourceProvenanceResult` contract and
included `provenance_executed` as part of that result. The field was
validated as a boolean, but its semantic relationship to a `usable` result
was not enforced.

## Verified gap

Before Step 195, this canonical shape was accepted:

```text
status = "usable"
sources = [valid SourceProvenance]
source_count = 1
provenance_executed = False
```

That state is internally contradictory: stable provenance records are exposed
while the result claims provenance assignment did not execute.

The contradiction matters downstream because `SourceObservationBuilder`
consumes provenance status and source records. It does not use
`provenance_executed` to decide whether source observations may be built. A
mapping-shaped provenance result could therefore deny execution while still
producing usable observations, freshness, confidence signals, and eventually a
Reality State.

## Safety invariant

evidence
→ source provenance
→ canonical source-provenance result
→ source observation
→ freshness
→ confidence
→ Reality State

If the canonical source-provenance result is `usable`, provenance assignment
must be recorded as executed:

```text
status == "usable"
→ provenance_executed is True
```

This prevents contradictory provenance execution metadata from entering the
observation/freshness path.

## Implementation

`SourceProvenanceResult.__post_init__()` now enforces:

- `provenance_executed` remains a boolean;
- when `status == "usable"`, `provenance_executed` must be `True`.

Existing validation remains intact for:

- nested `SourceProvenance` values;
- source-count/collection consistency;
- usable/empty/unavailable source shape;
- unavailable reasons;
- canonical source identity fields and identity method.

## Why empty and unavailable are not over-constrained

Step 195 deliberately does **not** require
`provenance_executed=True` for `empty` or `unavailable` results.

Those states contain no usable source-provenance records and therefore cannot
legitimately produce a positive downstream source-observation signal. They may
also represent a pipeline where provenance assignment was skipped or could not
run.

The existing production helpers and `SourceProvenanceBuilder` continue to use
their current execution semantics. Step 195 only prevents usable provenance
from denying execution.

## Mapping/deserialization integrity

`SourceProvenanceResult.validate()` reconstructs mapping-shaped provenance
through the canonical result constructor.

`SourceObservationBuilder` also reconstructs mapping-shaped provenance as a
`SourceProvenanceResult` before creating observations.

Therefore a mapping cannot bypass Step 195 by supplying
`status="usable"` together with `provenance_executed=False`.

## Compatibility

Normal production behavior is unchanged.

`SourceProvenanceResult.usable_result()` already uses the default
`provenance_executed=True`, and `SourceProvenanceBuilder` creates usable
results only after assigning stable source identities.

Step 195 preserves:

- Step 182 source-scoped provenance lineage;
- Step 188 source-observation timestamp bounds;
- Step 189 canonical observation timestamps;
- Step 190 fresh/stale classification integrity;
- Step 191 unknown freshness-policy integrity;
- Step 192 strict freshness count types;
- Step 193 freshness execution-state integrity;
- Step 194 source-observation execution-state integrity;
- existing confidence, claim, conflict, API, retrieval, and resource-limit
  semantics.

## Regression coverage

`backend/tests/test_step195.py` covers:

- direct rejection of usable provenance with `provenance_executed=False`;
- mapping/deserialization rejection;
- normalizer rejection;
- acceptance of usable provenance with execution `True`;
- rejection of non-boolean execution values;
- deliberate acceptance of explicitly non-executed empty/unavailable results;
- preservation of current helper semantics;
- standard observation-builder rejection of contradictory provenance mappings;
- retrieval-observation-builder rejection of contradictory provenance mappings;
- end-to-end valid provenance → observation → freshness compatibility;
- production provenance-builder execution semantics;
- non-regression of Steps 193 and 194.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation commit on `main`,
and the final synchronized `main` status commit.

## Deliberate non-goals

Step 195 does not broaden execution-state hardening into every older result
contract. Other boundaries should be changed only when their own downstream
contradiction is separately verified.

It also does not add publication-time inference, source-authenticity
verification, factual-truth scoring, new retrieval providers, persistence,
authentication, UI, monitoring, model/LLM judging, or autonomous behavior.
