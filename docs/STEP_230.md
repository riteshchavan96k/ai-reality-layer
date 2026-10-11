# Step 230 — Conservative Original-Source HTML Quotation-Context Guard

## Why this is next (repository-verified)

Step 229 final `main` was independently verified at `ac11ac547fbe245e2bcd618e726d480177ab0ae5`: 2,398 passing Python tests and four successful original-source/live claim workflows. On that code, `_VisibleHtmlText` emits visible text from HTML `<blockquote>` and `<q>` as ordinary text. Step 228/229's unique-unit and counterstatement guards operate on this flattened text. A client can submit a whole stand-alone quoted assertion and, if it matches the fixed Step 227 grammar, receive `aligned` even though the HTML publisher document marked it as a quotation, not an independently endorsed publisher assertion.

Step 230 is the narrow safety fix to retain quotation-origin context in the **real original-source HTML parser** and prevent those quoted units from receiving claim-alignment credit. It is not a semantic truth engine.

## Implementation

- Extend the original `_VisibleHtmlText` parser to track text contained by visible HTML `blockquote` and `q` tags, including nested inline elements, without modifying the original user-visible text or weakening hidden-HTML filters and structural paragraph barriers.
- Emit **SHA-256 digests** of normalized, newline-delimited quoted units in a backend-only observer response field `observed_quote_unit_sha256`. No quoted content is returned as new raw API output, and no new network read or external model is introduced.
- In existing claim-alignment mode ONLY, require the trusted backend reader's quote metadata to be a bounded list of valid digests. If missing, invalid, or if the submitted complete source unit hashes to a quoted unit, the source assurance fails closed with an explicit fixed reason and no positive attestation. A successful source-claim receipt records `source_quote_context_status=no_matching_html_quote_unit`, which the claim-alignment engine requires on all linked sources.
- The existing non-claim strict text-presence path is **unchanged** and does not emit the new claim-only quote-scope assessment.
- Preserve the original exact-URL allowlist, DNS/IP pinning, TLS chain/hostname checks, no redirects/no proxies, byte/time limits, capture SHA-256 and observed timestamps, source freshness, all Steps 221–229 safeguards, and historical Reality State response contracts.
- Backend injected reader fixtures explicitly declare empty quote digests for their *synthetic plain statements*, and real HTML tests inject transport beneath the actual source parser rather than fabricating positive attestation. The real publisher canary requires the backend-issued quote-scope status to show the genuine fixed Python.org heading was not quoted.

## Adversarial verification

New `backend/tests/test_step230.py` covers standalone blockquotes, inline `q`, nested HTML formatting, legitimate headings/paragraphs, quote-origin digest validation, missing metadata failure, hidden HTML context, unchanged historical text output and HTTP API refusal of caller overrides. `backend/app/evaluation/html_quote_origin_benchmark.py` has ten reviewer-written HTML cases (three legitimate nonquoted, seven quoted/duplicate adversarial) and is required in regular Python 3.13 CI.

## Boundaries and risks

This is **HTML quotation-scope integrity, not general semantic entailment, publisher endorsement or factual truth**. A publisher may quote or disclaim assertions without using `blockquote`/`q`; CSS-generated quotations, JavaScript DOM changes, semantic citations, natural-language attribution and quoted text in PDFs are not captured. A matching hash checks only recognized quote units. A source may still contain misinformation in ordinary unquoted paragraphs. Passing small synthetic and one historical live publisher canaries cannot estimate field accuracy. Do not mislabel `no_matching_html_quote_unit` as `publisher_authenticated` or `semantic_support_verified`.

## Acceptance gate

1. Entire Python 3.13 backend suite and every historical replay (Steps 217–229) plus Step 230 synthetic policy pass on final feature head.
2. Existing real original Python.org, genuine two-publisher Python.org+IANA, and actual source-backed claim-alignment HTTPS workflows pass on feature head with no source security relaxation.
3. PR is reviewed and merged; **all four** hosted workflows pass again on the exact independently merged `main` SHA, checking job logs for test totals and benchmark decisions.
4. Any docs-only final-status PR must also pass all four on its final exact merged `main` SHA. A checkmark is awarded only at that point.

## Status

Implementation under verification. No completed status asserted before exact final-main GitHub CI.
