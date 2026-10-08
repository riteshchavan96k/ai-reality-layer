# Step 199 — Canonical Claim-Extraction Execution-State Integrity

## Objective

Ensure a canonical claim-extraction result cannot expose usable candidate
claims while simultaneously claiming that extraction did not execute.

Step 154 established the canonical `ClaimExtractionResult` validation
boundary and included `extraction_executed`. The field was validated as a
boolean, but its semantic relationship to a `usable` result was not enforced.

## Verified gap

Before Step 199, this canonical shape was accepted:

```text
status = "usable"
claims = [valid EvidenceClaim]
source_count = 1
extraction_executed = False
```

That state is contradictory: it exposes extracted claims while declaring that
claim extraction did not execute.

The contradiction is downstream-relevant because both
`ClaimEvidenceLinker` and `ClaimConflictDetector` consume the claims/status
rather than using `extraction_executed` as a gate. A malformed canonical
extraction result could therefore deny execution while still producing:

- usable claim-evidence links;
- positive claim coverage;
- conflict-detection outcomes;
- confidence signals;
- a supported Reality State when the remaining grounding signals are healthy.

## Safety invariant

evidence
→ claim extraction
→ canonical claim-extraction result
→ claim-evidence linking / conflict detection
→ confidence
→ Reality State

The canonical rule is now:

```text
status == "usable"
→ extraction_executed is True
```

This prevents usable claims from contradicting their own execution metadata.

## Why empty and unavailable remain flexible

Step 199 deliberately does **not** require
`extraction_executed=True` for `empty` or `unavailable` results.

An `empty` extraction result contains no claims. Downstream linking therefore
cannot establish positive claim coverage from it.

An `unavailable` extraction result is explicitly propagated as unavailable by
the downstream claim-linking and conflict-detection stages.

Allowing those non-positive states to record `extraction_executed=False`
preserves the ability to represent skipped or unavailable extraction work
without inventing stricter semantics than the existing pipeline requires.

## Implementation

`ClaimExtractionResult.__post_init__()` now enforces:

- `extraction_executed` remains a boolean;
- when `status == "usable"`, `extraction_executed` must be `True`.

Existing validation remains intact for:

- canonical nested `EvidenceClaim` values;
- non-negative source count;
- usable/empty/unavailable claim shape;
- unavailable reasons;
- extraction-method and source-reference validation.

## Mapping/deserialization integrity

`ClaimExtractionResult.validate()` reconstructs mapping-shaped results through
the canonical result constructor.

`ClaimExtractionResultNormalizer` therefore inherits the same invariant.

The mapping intake paths in both `ClaimEvidenceLinker` and
`ClaimConflictDetector` also reconstruct `ClaimExtractionResult`, so a
mapping with usable claims and `extraction_executed=False` cannot proceed into
linking or conflict detection.

## Compatibility

Normal production behavior is unchanged.

`ClaimExtractionResult.usable_result()` already uses the default
`extraction_executed=True`.

`EvidenceClaimExtractor` creates usable results only after running its
deterministic extraction logic, and its existing empty/unavailable helper paths
also currently emit `True`.

Step 199 preserves:

- deterministic sentence-based claim extraction;
- Step 182 source-scoped claim lineage;
- Step 197 linked-claim count integrity;
- Step 198 linking execution-state integrity;
- Step 196 conflict execution-state integrity;
- Steps 188–195 provenance/observation/freshness integrity;
- confidence aggregation semantics;
- APIs, retrieval behavior, and resource limits.

## Regression coverage

`backend/tests/test_step199.py` covers:

- direct rejection of usable extraction with `extraction_executed=False`;
- mapping/deserialization rejection;
- normalizer rejection;
- acceptance of usable extraction with execution `True`;
- rejection of non-boolean execution values;
- deliberate acceptance of explicit non-executed empty/unavailable states;
- preservation of current helper semantics;
- claim-evidence-linker rejection of contradictory extraction mappings;
- conflict-detector rejection of contradictory extraction mappings;
- production extractor usable/empty/unavailable execution behavior;
- valid extraction → linking → supported-confidence compatibility;
- non-regression of Step-198 linking execution integrity;
- preservation of the existing usable-result claim requirement.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation commit on `main`,
and the final synchronized `main` status commit.

## Deliberate non-goals

Step 199 does not change the extraction algorithm, extraction-method semantics,
source-count semantics, claim deduplication behavior, linking algorithm,
conflict algorithm, or confidence formula.

It also does not add semantic extraction, LLM judging, embeddings,
publication-time inference, source-authenticity verification, factual-truth
scoring, new providers, persistence, authentication, UI, monitoring, or
autonomous behavior.
