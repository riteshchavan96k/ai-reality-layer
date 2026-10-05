# Step 185 — Bounded Developer-Submitted Claim Processing

## Roadmap justification

This milestone follows the explicit limits introduced in Step 184 for
*retrieved* evidence. Step 180 previously introduced a separate API accepting
up to 20 developer-submitted documents of up to 50,000 characters each.
Step 181 added explicit source observation freshness; Step 182 and Step 183
secured retrieved source attribution and freshness.

Step 184 imposed a 2,000-unique-claim cap per retrieved response. However,
the direct-submitted-evidence bundle calls the generic extractor once per
document and then merges the results. Even though each completed document
now inherits an existing per-document 2,000-claim guard, **there was no cap
across all submitted documents**. A legitimate-looking submission could
therefore produce tens of thousands of separate claims and links despite
passing the document-size and document-count limits. It also incorrectly
reported `retrieved_claim_limit_exceeded` when a directly supplied document
hit that per-document guard.

The original MVP document defines the evidence → claims → conflict/confidence
path but does **not** preassign a separate Step 185 title. This milestone
addresses the observed implementation gap instead of inventing a new feature
family.

## Implemented boundary

The direct-submission API `POST /api/v1/reality-state/evidence` and its
underlying `SubmittedEvidenceBundle.extract_claims` permit a maximum of
**2,000 unique candidate claims per submission**, across all documents.

- The number of *unique*, casefold-normalized candidate claims (matching
  the existing deterministic extractor merge key) counts against the
  limit. Repeated claims across sources retain each contributing original
  source URI without consuming a second unique claim slot.
- Exactly 2,000 unique claims are permitted.
- Attempting to insert the 2,001st distinct claim stops processing and
  returns a canonical `ClaimExtractionResult.unavailable_result`:
  `reason="submitted_claim_limit_exceeded"`, `claims=()`, with the
  original document source count. **No partial candidate claim graph** is
  returned to downstream linkage, conflict detection, or confidence.
- A single document individually exceeding the already-present
  2,000-candidate extractor budget is reported to submitted-evidence
  clients with that same **submitted**, not **retrieved**, reason.
- Existing per-document 50,000-character and 20-document validation
  remains unchanged. When the domain is called with a lazy or
  potentially infinite document iterable, it now consumes at most
  21 documents (one beyond the permitted limit) before rejecting it.
  This avoids creating an unbounded tuple from an invalid stream.
- Successful in-limit requests retain source-scoped extraction,
  exact-duplicate merging, first-seen ordering, observation timestamps
  and declared freshness semantics.

## Conservative Reality State

An over-budget submission is still evidence that the developer supplied;
it is **not** evidence that the submitted statements are false. Its
canonical Reality State retains the ordinary source metadata when valid,
but it does not claim to have successfully linked a partial subset:
extraction becomes unavailable, claim count is zero, there are no claim
links, conflict detection is unavailable, and aggregate confidence cannot
be `supported`. The existing Reality State builder and signal
aggregation determine the uncertainty/insufficiency status.

## Reuse rather than parallel code

- Reuse `MAX_RETRIEVED_CLAIMS` from
  `backend/app/reality/retrieval_input_bounds.py` as
  `MAX_SUBMITTED_CLAIMS` for a matching default policy.
- Reuse `EvidenceClaimExtractor` per document for deterministic sentence
  segmentation and intra-document duplicate merging; no new tokenizer or
  semantic truth classifier.
- Add a lightweight **global** unique-claim counter at the current
  cross-document merging boundary.
- Reuse existing claim, link, provenance, freshness, conflict, and
  confidence contracts.
- Do not change `EvidenceClaimExtractor.extract_result` for its
  legacy `status="usable"` lower-level call contract or modify Step
  184's retrieved evidence limit.

## Regression coverage

`backend/tests/test_step185.py` covers:
1. shared policy defaults;
2. exactly 2,000 claims from one and multiple documents;
3. 2,001 claims within a single document and across multiple documents;
4. canonical unavailable result and **zero** partial claims;
5. duplicate claims (case-insensitive and exact), per-source URI merging;
6. direct Reality State and HTTP handler no-partial-links and no
   supported-confidence outcomes;
7. small valid submitted evidence and conflict/freshness non-regression;
8. bounded 20/21-document processing of lazy and infinite iterables;
9. untouched generic `status="usable"` legacy extraction behavior.

The entire hosted backend regression suite must pass on the final
synchronized `main` commit. Do not mark the step complete based on an
unmerged branch, stale CI, or passing only the new tests.

## Security, compatibility and non-goals

This is a deterministic **resource-amplification safety** change on the
existing developer evidence API. It is not a source authenticity
verification mechanism, factual-truth check, model inference, a new
retrieval provider, a limit on arbitrary internal synthetic models, a
database/persistence feature, a real-world deployment or a general
network/server load test. 2,000 is an explicit per-request engineering
limit, not an epistemic guarantee or evidence quality threshold.
