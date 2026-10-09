# Step 208 — Submitted-Evidence Semantic Structuring Integrity

## Identification: verified regression after Step 207

Step 207 added a semantic structuring stage to `EvidenceClaimExtractor`
which correctly runs **after** that extractor's internal candidate claim
deduplication. The retrieval-based path already supplies all source-scoped
documents to one extractor invocation.

The developer-submitted evidence path took a different route in
`SubmittedEvidenceBundle.extract_claims`:

1. Call `extractor.extract_result` separately for each submitted document.
2. Merge the returned candidate claims with equal normalized text.
3. Reconstruct duplicate `EvidenceClaim` objects with text, references,
   and extraction method **but without `semantic_structure`**.

After Step 206/207, step (3) silently defaulted an already-structured claim
back to `unstructured` when the same claim appeared in two documents.
Furthermore, the optional semantic adapter was called independently per
source **before** global deduplication and global budget enforcement.
That could perform unnecessary inference or side effects for claims that
would later be rejected because the complete submission exceeded 2,000
unique candidate claims.

These are confirmed product correctness and resource-control issues, not
reasons to add a speculative interface or an irrelevant normalization class.

## Objective

Make submitted-evidence extraction share the existing source-scoped,
global-deduplication and semantic structuring order used by
`EvidenceClaimExtractor`, while preserving Step 180 and Step 185
input limits, failure contracts, provenance, and default behavior.

Canonical sequence:

```text
validated submitted documents
  -> existing SubmittedEvidenceBundle.to_evidence()
  -> existing EvidenceClaimExtractor.extract_result()
  -> source-scoped sentence candidate extraction
  -> global case-insensitive deduplication, with complete source_refs
  -> global unique-claim budget
  -> optional Step 207 semantic structurer, once per unique claim
  -> validated canonical EvidenceClaim objects / ClaimExtractionResult
```

## Implementation

Updated only `backend/app/reality/submitted_evidence.py` business logic.

- `extract_claims` still requires an `EvidenceClaimExtractor` instance.
- It now calls `extractor.extract_result(self.to_evidence())` **once**
  for the entire validated, source-scoped bundle.
- The existing extractor handles global duplicate merging **before** any
  semantic adapter invocation.
- This means the structurer receives the complete set of supporting source
  references for a candidate claim.
- It preserves `EvidenceClaim.semantic_structure`, canonical claim text,
  `extraction_method`, deduplicated source references, and the original
  claim order without independently reconstructing claims.
- The existing shared claim cap remains 2,000 unique candidate claims:
  `MAX_SUBMITTED_CLAIMS == MAX_RETRIEVED_CLAIMS`.
- If the extractor detects an over-budget graph, the submitted-evidence
  path still returns the historical reason
  `submitted_claim_limit_exceeded` instead of an inappropriate retrieved
  evidence error. It does not expose partial claims.
- Neither the public API shape nor `SubmittedEvidenceBundle` constructor
  or `to_evidence()` are changed.

This removes duplicate extraction logic rather than adding another
contract class.

## Safety properties

### Semantic correctness and honest uncertainty

A `structured` state still means a trusted adapter supplied a
schema-valid triple; it does **not** establish that the triple accurately
represents its source claim or that the claim is true.

The production default remains `unstructured` /
`semantic_structuring_not_attempted` with **no** model invocation.

If a trusted injected structurer returns malformed output, raises an
exception, or abstains, the Step 207 fail-closed semantics remain active
and preserve the attributed source claim.

### Global budgets are enforced before optional structuring

The extractor checks that the submitted document set has no more than
2,000 unique candidate sentences **before** invoking a semantic adapter.
A submission with 2,001 unique sentences from individually valid
documents returns `unavailable` with
`submitted_claim_limit_exceeded`, zero claims, and zero semantic
adapter calls.

The existing document-count and content-size restrictions remain
enforced at submission validation.

### Source provenance is not fabricated

The source-scoped evidence representation created by `to_evidence()`
contains each document's own URI and exact content. The extractor
deduplicates repeated sentences while preserving original URIs.

An API client-supplied URI is a **reported reference**, not independent
verification of publication authenticity or factual trustworthiness.

## Regression tests

`backend/tests/test_step208.py` covers:

1. Structured semantic metadata survives a duplicate claim across sources.
2. Exactly one semantic adapter call receives all supporting source refs.
3. The unconfigured default remains explicitly unstructured.
4. Case-insensitive duplicates preserve the first text and source order.
5. Adapter errors and malformed results do not erase merged attribution.
6. Exceeding the global 2,000-claim cap rejects **before** any adapter call.
7. Exactly 2,000 unique claims across repeated documents remain accepted.
8. Invalid extractor configurations remain rejected.
9. The actual submitted-evidence Reality State orchestration returns
   structured metadata with complete source lineage and evidence links.
10. The ordinary unconfigured orchestration path remains honest.

Existing Step 180, 184, 185, 187, 206, and 207 tests must also pass.

## Explicit exclusions

Step 208 does not add Hugging Face, ML, DL, LLM inference, new
retrieval providers, entity resolution, semantic correctness
certification, database persistence, new API fields, or changes to
existing conflict/freshness/confidence engines.

Those features remain future work, each justified by separate product
requirements and evaluation.

## Completion requirements

Implement on a separate branch, pass the **complete** Python 3.13
GitHub-hosted backend suite, merge through a PR, verify the merged
implementation on `main`, and synchronize the repository status with
verified checks. Do not claim completion before those checks succeed.
