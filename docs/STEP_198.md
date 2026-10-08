# Step 198 — Canonical Claim-Evidence Linking Execution-State Integrity

## Objective

Ensure a canonical claim-evidence linking result cannot expose usable links
and full claim-evidence coverage while simultaneously claiming that linking did
not execute.

Step 155 introduced the canonical `ClaimEvidenceLinkingResult` contract and
its `linking_executed` flag. The flag was validated as a boolean, but its
semantic relationship to a `usable` result was not enforced.

## Verified gap

Before Step 198, this canonical shape was accepted:

```text
status = "usable"
links = [valid claim-evidence link]
claim_count = 1
linked_claim_count = 1
linking_executed = False
```

That state is contradictory: it exposes a completed claim-evidence relationship
and can report full coverage while declaring that linking never executed.

The contradiction matters downstream because
`RealityConfidenceSignalAggregator` calculates claim coverage from
`claim_count` and `linked_claim_count`. It does not use
`linking_executed` when deciding whether full coverage may support the
Reality State.

A malformed canonical linking result could therefore deny execution while
still contributing a supported confidence signal.

## Safety invariant

claims + evidence
→ claim-evidence linking
→ canonical linking result
→ claim coverage
→ confidence
→ Reality State

The canonical rule is now:

```text
status == "usable"
→ linking_executed is True
```

This guarantees that usable claim-evidence links and their positive coverage
signal cannot contradict their execution metadata.

## Why empty and unavailable remain flexible

Step 198 deliberately does **not** require
`linking_executed=True` for `empty` or `unavailable` results.

An `empty` linking result has zero linked claims. Its coverage is therefore
zero when claims exist, or undefined when no claims exist. It cannot create
full supported claim coverage.

An `unavailable` result is explicitly treated as unavailable by downstream
confidence and contributes uncertainty.

Allowing those non-positive states to record `linking_executed=False`
preserves the ability to represent skipped or unavailable work without
inventing stricter semantics than the pipeline currently requires.

## Implementation

`ClaimEvidenceLinkingResult.__post_init__()` now enforces:

- `linking_executed` remains a boolean;
- when `status == "usable"`, `linking_executed` must be `True`.

All existing Step-197 linked-claim count integrity remains intact:

- non-negative counts;
- `linked_claim_count <= claim_count`;
- declared linked-claim count must equal the number of distinct
  case-insensitive claim texts represented by `links`.

Existing status/link/reason consistency also remains unchanged.

## Mapping/deserialization integrity

`ClaimEvidenceLinkingResult.validate()` reconstructs mapping-shaped inputs
through the canonical result constructor.

`ClaimEvidenceLinkingResultNormalizer` inherits the same invariant.

Therefore mappings cannot bypass Step 198 by supplying a usable result with
`linking_executed=False`.

## Confidence integrity

The confidence formula is unchanged.

A legitimate usable linking result with complete coverage still participates
normally in supported confidence.

Step 198 only ensures that a canonical result capable of providing positive
claim-evidence coverage must also record that linking actually executed.

The protected boundary is:

```text
canonical links
→ verified linked-claim count
→ executed usable linking
→ claim coverage
→ confidence signals
→ Reality State
```

## Compatibility

Normal production behavior is unchanged.

`ClaimEvidenceLinkingResult.usable_result()` uses the default
`linking_executed=True`.

`ClaimEvidenceLinker` creates usable results only after actually building
links and currently emits executed empty/unavailable helper results as well.

Step 198 preserves:

- Step 155 deterministic claim-evidence linking behavior;
- Step 182 source-scoped claim lineage;
- Step 197 linked-claim count integrity;
- Step 196 conflict execution-state integrity;
- Steps 188–195 provenance/observation/freshness integrity;
- existing confidence formula and policy;
- APIs, retrieval behavior, and resource limits.

## Regression coverage

`backend/tests/test_step198.py` covers:

- direct rejection of usable linking with `linking_executed=False`;
- mapping/deserialization rejection;
- normalizer rejection;
- acceptance of usable linking with execution `True`;
- rejection of non-boolean execution values;
- deliberate acceptance of explicit non-executed empty/unavailable states;
- preservation of current empty/unavailable helper semantics;
- production linker usable and empty execution behavior;
- supported confidence compatibility for valid executed full coverage;
- blocking a non-executed full-coverage result before confidence;
- preservation of Step-197 linked-claim count integrity.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation commit on `main`,
and the final synchronized `main` status commit.

## Deliberate non-goals

Step 198 does not change the claim-evidence linking algorithm, linked-claim
count semantics, source-count semantics, or the confidence formula.

It also does not harden claim-extraction execution state in this step; that is
a separate upstream boundary and should only be changed as a separately
verified step.

No semantic evidence matching, LLM judging, embeddings, publication-time
inference, source-authenticity verification, factual-truth scoring, new
providers, persistence, authentication, UI, monitoring, or autonomous behavior
is introduced.
