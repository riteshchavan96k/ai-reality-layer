# Step 196 — Canonical Claim-Conflict Execution-State Integrity

## Objective

Ensure canonical claim-conflict results cannot report meaningful conflict
outcomes while simultaneously claiming that conflict detection did not
execute.

Step 156 introduced the canonical `ClaimConflictResult` contract and its
`detection_executed` flag. The flag was validated as a boolean, but its
semantic relationship to `usable` and `empty` results was not enforced.

## Verified gap

Before Step 196, both of these contradictory canonical shapes were accepted:

```text
status = "usable"
conflicts = [detected conflict]
conflict_count = 1
detection_executed = False
```

and:

```text
status = "empty"
conflicts = []
conflict_count = 0
detection_executed = False
```

The second case is especially important. In this repository, an `empty`
conflict result means conflict detection completed and found no conflicts.
Downstream confidence aggregation treats zero conflicts as a positive signal
when the rest of the grounding path is healthy.

Therefore an `empty` result cannot safely mean both "no conflicts detected"
and "detection did not execute."

## Safety invariant

claims
→ conflict detection
→ canonical conflict result
→ confidence signals
→ Reality State

The canonical execution-state rule is now:

```text
status in {"usable", "empty"}
→ detection_executed is True
```

Only `unavailable` may explicitly record
`detection_executed=False`.

This preserves the distinction between:

- detection ran and found one or more conflicts;
- detection ran and found zero conflicts;
- conflict detection was unavailable or did not run.

## Implementation

`ClaimConflictResult.__post_init__()` now enforces:

- `detection_executed` must remain a boolean;
- `usable` requires `detection_executed=True`;
- `empty` requires `detection_executed=True`;
- `unavailable` may retain either boolean execution state as long as all
  existing unavailable-result invariants are satisfied.

Existing validation remains intact for:

- nested `ClaimConflict` records;
- non-negative counts;
- conflict-count/collection consistency;
- status/conflict-shape consistency;
- unavailable reasons.

## Why empty is stricter than previous execution-integrity steps

Steps 193–195 deliberately left `empty` flexible for freshness,
source-observation, and source-provenance results because those empty states
contain no positive data that can establish a supported downstream signal.

Conflict detection is different.

An `empty` conflict result semantically means:

> conflict detection executed and found no candidate conflicts.

The confidence aggregator can treat that as part of a supported result.
Therefore `empty + detection_executed=False` would be a direct semantic
contradiction that could falsely behave like successful conflict checking.

## Mapping/deserialization integrity

`ClaimConflictResult.validate()` reconstructs mapping-shaped inputs through
the canonical result constructor.

`ClaimConflictResultNormalizer` therefore inherits the same invariant.

A canonical mapping cannot bypass Step 196 by supplying `usable` or `empty`
with `detection_executed=False`.

## Compatibility

Normal production behavior is unchanged.

`ClaimConflictDetector` already uses:

- `usable_result()` after detecting one or more explicit deterministic
  conflicts;
- `empty_result()` after detection runs and finds no conflicts;
- `unavailable_result()` when claim extraction is unavailable.

Those helper paths currently retain `detection_executed=True`, so Step 196
hardens malformed direct/mapping construction without changing normal detector
behavior.

Step 196 preserves:

- deterministic explicit-negation conflict semantics;
- Step 182 source-scoped claim lineage;
- Steps 188–195 provenance/observation/freshness invariants;
- downstream confidence policy;
- retrieval, evidence, API, and resource-limit behavior.

## Regression coverage

`backend/tests/test_step196.py` covers:

- direct rejection of usable non-executed conflict results;
- direct rejection of empty non-executed conflict results;
- mapping/deserialization rejection for both states;
- normalizer rejection;
- acceptance of executed usable and empty results;
- rejection of non-boolean execution values;
- deliberate acceptance of unavailable non-executed results;
- preservation of current unavailable helper behavior;
- production detector conflict and zero-conflict execution semantics;
- production detector unavailable behavior;
- supported confidence compatibility for a valid executed empty conflict result;
- uncertain confidence for unavailable/non-executed conflict detection;
- preservation of conflict-count consistency.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation commit on `main`,
and the final synchronized `main` status commit.

## Deliberate non-goals

Step 196 does not change the confidence aggregation algorithm or make the
aggregator itself a canonical conflict normalizer. It hardens the canonical
`ClaimConflictResult` boundary only.

It also does not add semantic contradiction inference, publication-time
inference, source-authenticity verification, factual-truth scoring, new
providers, persistence, authentication, UI, monitoring, model/LLM judging, or
autonomous behavior.
