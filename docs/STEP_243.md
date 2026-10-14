# Step 243: bounded two-host original-source answer comparison

## Verified predecessor and the missing product capability

Independently refetched main SHA 303610b98d18c220cde6c10a15853a16d6690fc9
and all 16 successful GitHub Actions push workflows on that exact commit.
Step242 is the accepted milestone (2,814 full backend tests, 39 Step242
dedicated tests). No pre-existing Step243 specification was found. The product
could verify and deliver a citation from one source, but could not compare
two separately observed source statements for the SAME claim. Earlier Step226
sourced two publisher sites for different test observations; it was NOT
a two-source same-claim corroboration endpoint.

## Actual Step243 scope

- Opt-in authenticated POST /api/v1/reality-state/answer/compare for a
  narrow explicit claim, explicit entity, exactly two exact HTTPS URL candidates
  and a positive finite maximum age. Both URLs must already be operator-allowed,
  and hostnames must differ. Duplicate hostnames are a validation error.
- Before any network read, reject an unauthorized second source. Reuse each
  source's existing Step241 once-observed original-source verification and
  Step242's strict answer/quote/request-binding/freshness consumer independently.
  At most one original HTTPS read per URL; no arbitrary discovery, no LLM.
- Only if BOTH complete source observations validate, expose TWO individually
  attributed original statements, source links, SHA-256 quote and capture
  receipts, UTC capture times and a bound pair-level request digest.
  Two alignments -> two_source_alignment. Two contradictions ->
  two_source_contradiction. Mixed -> source_disagreement. Only two alignments
  enable may_use_as_bounded_evidence, and ONLY as narrow observed text evidence.
  Disagreement always forbids a positive decision.
- Any missing, stale, quoted, ambiguous, forged, off-list or failed observation
  aborts the pair, suppresses BOTH citations, URLs and partial capture metadata.
  Pilot bearer authentication is unchanged; no external deployment.
- Regressions include valid double alignment, double contradiction, disagreement
  both directions, source failures, quotes, tampering, freshness, SSRF-style
  invalid URLs, off-list early rejection, bad bearer, and old API compatibility.
- Seventeenth Actions workflow exercises the authenticated actual API. Its
  real publisher test fetches Python.org and IANA over separately verified
  HTTPS, and MUST ABSTAIN because IANA does not contain the Python release
  assertion. It proves correct refusal, NOT real positive two-site corroboration.
  Positive dual-host cases use deliberately mocked original text and are NOT
  evidence of two real publisher claims agreeing.

## Nonclaims and safety

Two distinct hostnames do NOT prove independent ownership, editorial
independence, publisher authenticity, or different upstream sources. Even two
aligned texts are NOT independent factual truth, publisher signatures,
semantic generalization, or broad QA. No user-supplied quote is trusted.
Observed source quotations remain untrusted data and must be HTML escaped.
The single-claim deterministic grammar, freshness and quote/counterstatement
guards remain the existing conservative gates; neural NLI cannot promote
negative or incomplete source evidence. No unsupervised LLM, source web search,
arbitrary retrieval, unrestricted autonomous actions, or public hosting.

Step234 external HTTPS deployment is deferred at owner instruction. GitHub
release issue #242 remains open and is NOT engineering Step242.

## Acceptance requirement

This implementation is provisional until merge and exact-final-main validation:
all 17 GitHub Actions push workflows must be successful on the exact final
main commit; independently inspect backend full regression test logs,
Step243 test logs and the genuine two-host HTTPS canary. Record acceptance
in PR comments without another unverified git edit. Only then Step243 ✅.

## Example API request

Submit the following JSON to the authenticated comparison endpoint using a
valid operator-managed pilot bearer token:

    {
      "claim_text": "Python 3.13.0 is a stable release.",
      "entity": "Python 3.13.0",
      "source_uris": [
        "https://www.python.org/downloads/release/python-3130/",
        "https://www.iana.org/domains/reserved"
      ],
      "freshness_max_age_seconds": 3600
    }

This deliberately irrelevant second source must cause abstention, not
fabricated agreement. A real two-alignment response requires independently
eligible pages at two operator-allowed distinct HTTPS hostnames.
