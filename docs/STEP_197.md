# Step 197 — Canonical Claim-Evidence Linked-Claim Count Integrity

## Objective

Ensure a canonical claim-evidence linking result cannot report more or fewer
linked claims than are actually represented by its canonical link records.

Step 155 introduced `ClaimEvidenceLinkingResult` and the
`linked_claim_count` field. The production helper already defines this count
as the number of distinct case-insensitive claim texts represented by the
result's links, but direct construction and mapping normalization did not
enforce that relationship.

## Verified gap

Before Step 197, a canonical result could contain one linked claim while
declaring two linked claims:

```text
status = "usable"
links = [link for claim A]
claim_count = 2
linked_claim_count = 2
```

It could also contain no links while declaring a linked claim:

```text
status = "empty"
links = []
claim_count = 1
linked_claim_count = 1
```

Both shapes were internally inconsistent.

The risk is downstream confidence aggregation. Claim coverage is calculated as:

```text
linked_claim_count / claim_count
```

Therefore an overstated canonical `linked_claim_count` could turn partial or
missing claim-evidence linkage into apparent 100% coverage.

## Canonical invariant

The result now derives the actual linked-claim count from its canonical links
using the same rule already used by `usable_result()`:

```text
actual_linked_claim_count =
    number of distinct case-insensitive link.claim_text values

linked_claim_count == actual_linked_claim_count
```

This preserves the existing meaning that multiple evidence links for the same
claim still represent one linked claim.

Examples:

- claim A linked to source 1 → linked count 1;
- claim A linked to source 1 and source 2 → linked count 1;
- claim A and claim B linked → linked count 2;
- no links → linked count 0.

## Implementation

`ClaimEvidenceLinkingResult.__post_init__()` now:

1. validates the existing non-negative count rules;
2. preserves the existing rule that `linked_claim_count <= claim_count`;
3. derives the number of distinct linked claim texts from `links`;
4. requires the declared `linked_claim_count` to exactly match that derived
   value;
5. continues with the existing execution/status/reason invariants.

No count coercion or inference from unrelated evidence fields is introduced.

## Mapping/deserialization integrity

`ClaimEvidenceLinkingResult.validate()` reconstructs compatible mappings
through the canonical result constructor.

`ClaimEvidenceLinkingResultNormalizer` therefore inherits the same invariant.

A mapping cannot bypass Step 197 by supplying an inflated or understated
`linked_claim_count`.

## Confidence integrity

The confidence aggregator continues to calculate coverage from canonical
linking counts.

Step 197 guarantees that a canonical full-coverage count cannot be created
unless the canonical link collection actually represents that many distinct
claims.

This hardens the existing:

```text
claim/evidence links
→ linked-claim count
→ claim coverage
→ confidence signals
→ Reality State
```

boundary without changing the confidence formula.

## Compatibility

Normal production behavior is unchanged.

`ClaimEvidenceLinkingResult.usable_result()` already calculates
`linked_claim_count` from distinct case-insensitive linked claim texts.
`empty_result()` already emits zero linked claims.

`ClaimEvidenceLinker` uses those canonical helpers, so valid production
outputs already satisfy the new invariant.

Step 197 preserves:

- Step 155 deterministic claim-evidence linking behavior;
- Step 182 source-scoped claim lineage;
- Step 196 conflict execution-state integrity;
- all provenance/observation/freshness integrity from Steps 188–195;
- existing confidence aggregation semantics;
- APIs, retrieval behavior, and resource limits.

## Regression coverage

`backend/tests/test_step197.py` covers:

- rejection of overstated linked-claim counts;
- rejection of understated linked-claim counts;
- rejection of inflated counts on empty results;
- mapping/deserialization rejection;
- normalizer rejection;
- multiple links for one claim counting as one linked claim;
- case-insensitive duplicate claim text counting as one;
- two distinct linked claims requiring count two;
- helper-constructor semantics;
- empty-result zero-count semantics;
- production linker consistency;
- supported confidence with legitimate full coverage;
- blocking false full coverage before confidence;
- preservation of the existing count-overflow guard.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation commit on `main`,
and the final synchronized `main` status commit.

## Deliberate non-goals

Step 197 does not change the claim-evidence linking algorithm, the confidence
formula, source-count semantics, or linking execution-state semantics.

It also does not add semantic evidence matching, LLM judging, embeddings,
publication-time inference, source-authenticity verification, factual-truth
scoring, new providers, persistence, authentication, UI, monitoring, or
autonomous behavior.
