# Step 228 — Original-Source Context Integrity for Claim Alignment

## Repository-verified defect

Step 227's latest independently green `main` is `f8287c13e95c4fec017bf709d59d1ab9d20fed7c` (2,343 backend tests, three earlier genuine HTTPS workflows and a Step 227 live claim canary). Step 227 checks whether a *client-submitted excerpt* is exactly contained somewhere within backend-observed source text, then parses the isolated excerpt for a bounded claim. It does not check the text surrounding that excerpt **in the publisher's actual observed content**. An attacker can submit the middle of a negated or reported sentence and obtain an `aligned` claim despite the full observed text saying the opposite. The source reader had already observed that surrounding text; Step 228 uses it **within the same backend-owned read**.

## Implemented scope

1. `IndependentSourceTextAssurance.check(..., require_unique_standalone_unit=True)` is invoked only for `require_claim_alignment=True`; the legacy text-presence opt-in and default API behavior are unchanged. It does not make extra requests or expand the operator allowlist.
2. After verifying the excerpt exists in independently read text, the backend demands that the exact excerpt occur **once and only once** in the complete retrieved text and occupy an entire structural text unit. The HTML reader already preserves conservative newline barriers between paragraphs, headings, list items, tables and hidden elements (Steps 224/225). For plaintext, these are whole newline-delimited lines. Whitespace around each entire unit is tolerated; there is **no case folding or fuzzy text reconstruction**.
3. An embedded substring, a paragraph with extra reporting/negating words before or after it, multiple occurrences, a cross-unit claim, or an independently unavailable original source fails closed with `excerpt_not_unique_standalone_source_unit` and **no successful capture hash/time** for that unsuccessful assurance. The backend emits only a fixed `assertion_context_status` code, not publisher HTML or surrounding text.
4. The Step 227 claim-alignment engine now demands an actual backend-issued `assertion_context_status=unique_standalone_unit` on every source. A bare source-text attestation without that field cannot grant alignment.
5. A new adversarial in-process FastAPI test suite and source-content replay cover embedded negatives/quotations/reporting, duplicates, legitimate standalone excerpts, server-owned capture metadata and compatibility. The existing Step 227 corpus is run through the **actual synthetic backend reader**, not a fabricated client-authoritative receipt.
6. The existing genuine live Python.org Step 227 workflow now requires the real original heading excerpt to pass this new source-unit integrity check. Step 222's single-publisher and Step 226's two-publisher HTTPS workflows remain unchanged. Both still exercise real DNS/TLS/network under exact operator allowlists.

## Explicit limits

This is a **source-text structural integrity** gate, not a full semantic context verifier, publisher authorship proof, browser DOM execution, signed provenance, world-fact correctness, independent annotated dataset, or production factual reliability. A standalone publisher paragraph may itself be false, misleading, a quote without markers, or refuted in a different paragraph; this guard **cannot** resolve that. Exact unit matching intentionally rejects some legitimate partial quotations, including prose sentences embedded inside longer paragraphs; this is a documented conservative restriction on the opt-in claim-alignment mode, not a default API regression. The main `supported` state still represents the historical structural confidence contract, **not** verified objective truth. Do not call a synthetic benchmark an estimate of population accuracy.

## Reproduction

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.claim_alignment_benchmark
python -m backend.app.evaluation.observed_context_benchmark
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.independent_source_assurance_benchmark
python -m backend.app.evaluation.capture_freshness_benchmark
python -m backend.app.evaluation.html_visibility_quality_benchmark
python -m backend.app.evaluation.structural_quote_benchmark
```

Accept only when new adversarial tests and replay, all historical tests/replays, the original publisher live HTTPS workflow, two-publisher live HTTPS workflow **and Step 227 live original-source claim workflow** pass on the final feature SHA and independently merged `main`. If a documentation-only final sync is merged, all four must pass again on its exact new `main` SHA. Never relax the source reader's DNS/TLS/IP, no-redirect, exact-URL, byte/time or output limits to force acceptance.

## Verification status

## Verified independently merged implementation CI

The source-backed Step 228 feature [PR #233](https://github.com/riteshchavan96k/ai-reality-layer/pull/233) merged into `main` as commit `aa2284b71056010a2b89ec1a2c8dc35d14868221`. All four workflows succeeded on **that exact commit**, verified from GitHub workflow records, job steps, and logs:

- [Full Python 3.13 backend CI 38166648475](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38166648475): **2,371 tests passed**, compilation and all older replays; 16/16 Step 227 policy outcomes and 13/13 Step 228 original-source context outcomes. The **13 synthetic Step 228 cases** contain three legitimate standalone units preserved and ten embedded/duplicated forged contexts abstained, 0/10 incorrectly aligned. These are hand-authored fixtures, **not** a population semantic/factual accuracy study.
- [Original publisher real HTTPS 38166648364](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38166648364): success, existing Step 222 canary unchanged.
- [Original Python.org + IANA two-publisher real HTTPS 38166648400](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38166648400): success, 3/3 authentic and 0/3 forged structurally supported in the six predefined cases.
- [Step 227 real original-source claim canary 38166648447](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38166648447): success, fixed genuinely retrieved Python.org release heading retained `unique_standalone_unit` evidence metadata and supported one limited positive proposition; its directly negated proposition was downgraded. No raw source HTML emitted.

An earlier feature-branch backend run correctly failed on a historical fixture that still expected a multi-line client excerpt to count as valid claim-mode source assurance. The fixture was updated to **expect fail-closed behavior**, without weakening the new check. The final feature head and merged main then passed all four checks.

**Engineering implementation acceptance is verified on `aa2284b...`.** The final *documentation-only* status synchronization still needs four successful workflows on its independently merged final `main` commit before marking that new HEAD fully green. Step 228 does not solve cross-paragraph refutation, real human reading context, publisher-authored truth, semantic inference or production accuracy.

