# Step 232 — Versioned Original-Source Claim-Safety Evaluation (✅ scoped engineering complete)

## Evidence-based milestone identification

The final completed predecessor is [Step 231](STEP_231_ENGINEERING_SCORECARD.md) at exact final merged `main` SHA `d2acf37f526a60bdfb4731947beb17f082379ccb`, with 2,440 Python tests and **five** successful real-source/HTTP CI workflows. This was confirmed directly from the repository before Step 232 scope was defined.

**No pre-existing Step 232 or agreed numeric roadmap file exists.** Rather than inventing a historical step, this document records a new, narrow scope derived from the documented Step 230/231 limitation: real-source canaries covered only a few fixed favorable assertions while the project had no versioned live claim-level challenge corpus with a transparent false-support/abstention scorecard. A large LLM integration without a measured baseline would undermine evidence reliability. The user's stated priority is a **genuinely correct AI Reality Layer**, not arbitrary numbered progress.

## Implemented intended scope (bounded)

1. Add a **fixed versioned, immutable-case-ID challenge manifest** (`backend/evaluation_fixtures/step232_original_source_claim_v1.json`) with **12 predeclared cases**, two original-publisher HTTPS hosts (Python.org and IANA), and a mix of a supported claim, a developer-identified true claim outside present grammar, contradictory, unrelated, hedged, forged, partial and cross-source misattribution cases. Individual claims/excerpts are specified **before** CI observes live pages.
2. Run all 12 using the **existing FastAPI evidence API and the actual allowlisted original-source HTTPS reader**, with opt-in exact URL allowlist, independent DNS/IP/TLS verification, no redirects/proxies, capture digests, and UTC observation times. Explicit `--live` is required; default CLI refuses network execution. No new external dependencies, unrestricted search, model outputs, hosted deployment, user-controlled URLs or secrets.
3. Reject a change that unexpectedly marks **any of the ten predeclared nonpositive/ambiguous claims `supported`**, or changes the expected finite-grammar alignment, source identity, unverified semantic/publisher flags, evidence receipt or API response. Also require the one fixed known-supported positive to remain supported. This is an **engineering regression gate** only.
4. Record the **second positive reference claim** (the correct human-understandable Python release date vs its abbreviated official excerpt) as deliberately **not supported** by the current atomic grammar. This is an explicit candidate for future semantic/NLI model evaluation; no fabricated model understanding.
5. Report auditable **digest/time only** captures, classifications, two developer-authored reference-positive cases, observed positive coverage, abstentions and false-support count. Do **not** publish raw HTML, raw excerpts, credentials or the full request payload. Include an honest machine-readable `developer_labeled_NOT_independently_human_reviewed` limitation.
6. Keep old Step 217–231 behavior, 2,440 historic tests and **five existing** CI workflows working unchanged. Add unit tests preventing label manipulation, false supported outcomes, provenance spoof, false claims of semantic/authorship truth and implicit network calls; add a sixth GitHub-hosted genuine original-HTTPS workflow.

## Acceptance — engineering policy benchmark, not factual dependability

- Original Step 231 exact-main milestone and [external HTTPS deployment release gate #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242) remain untouched and open respectively.
- Full Python 3.13 regression suite green **on final Step 232 PR HEAD and again on exact final merged main SHA**. Historical synthetic benchmarks still pass.
- All **six** GitHub Actions workflows, including new Step 232 real HTTPS 12-case evaluation, succeed on **exact merged main**. Independently inspect job logs; require the new policy report to identify 12 cases, two hosts, **0 / 10 developer-labeled nonpositive cases incorrectly supported** and explicitly show **only 1 / 2 developer-labeled positive claims supported** by this limited parser.
- Fixed original source content drift or source outage **fails** the live CI rather than fabricating an observation. Failures can be availability or page change, not proof of a code bug; inspect and update labels only with review and new fixture version.
- Preserve a closing PR comment with commit SHA, workflow IDs, actual log evidence and explicit limitations. **No checkmark based on a locally fabricated fake source**, synthetic-only replay or a green feature branch.

## Interpretation / scientific honesty

This is not independently human-labeled data: examples and expected outcomes were predeclared by the developer/assistant, not sampled randomly or rated by blinded independent annotators. **Neither 0/10 safety errors nor 1/2 positive coverage is a population accuracy, precision, recall or calibrated confidence statistic.** Both hosts are the **same two** earlier official publishers and the canonical positive remains the existing Python 3.13.0 release sentence. Some adverse cases are deliberately artificial. The system still uses a narrow parser and opt-in exact allowlists, and does **not** provide independent cryptographic publisher content attestation, universal entailment, arbitrary real-time search or factual truth guarantees.

A future, independently human-reviewed, domain-diverse dataset and broader original publishers remain required before recommending a model for real-world factual dependability. Do not call this an ML, deep-learning, Hugging Face or LLM integration. The evaluation supplies a measurable gating tool **for comparing** future model candidates.

## Local reproduction

```bash
python -m compileall -q backend/app
python -m pytest
# Only on a trusted network with an explicitly operator-configured exact two-URL allowlist:
export ARL_INDEPENDENT_SOURCE_ALLOWED_URLS='["https://www.python.org/downloads/release/python-3130/","https://www.iana.org/domains/reserved"]'
python -m backend.app.evaluation.step232_source_claim_safety --live
```

The live smoke executes in development mode **inside trusted CI on loopback**, not as a publicly reachable unauthenticated API. The public-facing auth and HTTPS ingress deployment issue #242 stays open. The verified implementation-main outcomes and measured limitations are preserved in [Step 232 Scorecard](STEP_232_SCORECARD.md).

## Exact merged-main acceptance status — scoped engineering ✅

[Implementation PR #245](https://github.com/riteshchavan96k/ai-reality-layer/pull/245) merged to `main` `06307e533ea44e5d0ac76a93c0641b6f584a1001`. All **six** new `push` jobs on that exact SHA completed successfully:

- [Backend 38362081385](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38362081385): 2,457 Python 3.13 tests pass, historical evaluation replays unchanged.
- [Step 232 real Python.org + IANA claim-safety challenge 38362081256](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38362081256): 12/12 expected finite-policy outcomes; 1 of 2 predeclared positive claims supported, 1 conservatively abstained, 0 of 10 developer-labeled nonpositive cases supported.
- [Real authenticated Docker HTTP 38362081358](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38362081358): success.
- [Real Python.org HTTPS 38362081352](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38362081352): success.
- [Real two-publisher HTTPS 38362081287](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38362081287): success.
- [Real bounded claim HTTPS 38362081244](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38362081244): success.

The initial feature-head full backend job failed because a new test mistook a **scenario ID containing the word `excerpt`** for a leaked publisher excerpt. The report deliberately contains scenario IDs but no raw source excerpts. The test was corrected; 2,457 tests and all six workflows passed on the final feature head and final implementation main. See [scorecard](STEP_232_SCORECARD.md). This documents a real engineering outcome, **not independent human-labeled field accuracy**. External-hosted release blocker #242 remains open.

This closing documentation change must itself pass all six workflows on its final merged main SHA to keep the current branch verified.
