# Step 233 — Safe, Machine-Readable Claim Decision Reasons (✅ scoped engineering complete)

## Verified predecessor and gap

The latest completed milestone prior to this change was **Step 232** at exact merged `main` `65c604bb64a5c8b83529aaaee2de1b5995b13425`, with 2,457 Python tests and all six successful exact-main real original-source CI workflows. This was checked through GitHub before starting. **No `docs/STEP_233.md` or previous numbered Step 233 roadmap file existed.** The scope here is a new, explicitly recorded continuation derived from the next verifiable product gap, not a fabricated pre-existing plan.

Step 232's fixed original-source evaluation found that **one of two developer-labeled valid propositions safely abstains** because it asks whether Python 3.13.0 was released on a full-text date while the independently observed source presents the excerpt `Release date: Oct. 7, 2024`. The claim-alignment response provided only `insufficient`: a downstream AI developer could not distinguish unsupported source grammar from unsupported claim grammar, missing independently observed evidence, or mismatched atomic assertions. **Do not automatically accept unscoped date labels as proof of subject/date entailment**; that would introduce a new false-support failure.

## New functional capability and scope

Extend the existing **opt-in strict original-source claim alignment** response with an *additive* `evidence.claim_alignment.decision_reasons` list. Each item contains only the **same source_ref as the existing decision** and a deterministic, bounded `code`, with no new inferred facts, source bytes, raw transport errors, tokens, or user-submitted text.

Accepted reason codes (fixed in the implementation, not interpolated from reader exceptions):

| Reason | Interpretation |
| --- | --- |
| `bounded_assertion_aligned` | Previously verified unique standalone original-source unit aligned under narrow grammar |
| `bounded_assertion_contradicted` | Previously verified atomic contradiction under the same restricted grammar |
| `source_grammar_unsupported` | Claim parses but the independently observed and validated **source excerpt** does not match our narrow atomic grammar; e.g. an unscoped release-date label |
| `claim_grammar_unsupported` | The proposed claim is hedged, otherwise unparseable or outside the bounded grammar |
| `atomic_relationship_undetermined` | Both parse but their bounded subject/predicate/value comparison does not prove match or contradiction |
| `independent_source_unverified` | Independent exact source observation or valid strict source assurance not available |
| `source_quoted_unit` | Source-side HTML unit identified as quoted; refuse to attribute the claim to the publisher |
| `source_counterstatement_observed` | Existing conservative source counterstatement guard blocked support |
| `source_assertion_context_unverified` | Strict source unit/context checks do not establish a unique clear assertion |
| `source_capture_receipt_invalid` | Missing/malformed digest/time receipt required for independent strict alignment |

This change is **diagnostic only**: it must never transform an `insufficient` into `aligned` or claim any unverified semantic/factual truth. Existing `source_decisions`, overall `status`, contract, source allowlist, authentication and model gates must remain unchanged.

## Implementation and real verification

- Add reason codes to `backend/app/reality/claim_assertion_alignment.py` without modifying existing source decisions or safety checks.
- Extend Step 232 audit to **verify** one allowed reason/source identity per scenario and output the enum code, not source bytes or sensitive exception strings.
- Add an independent `backend/app/evaluation/step233_source_reason_live_smoke.py` audit with **12 predeclared code expectations** based on the unchanged original Step 232 fixture. Running it with `--live` performs actual original Python.org and IANA DNS/IP-pinned TLS/HTTPS and FastAPI strict API calls. The known positive date abstention must report `source_grammar_unsupported`, not falsely become supported.
- Add `backend/tests/test_step233.py` unit tests for normal, contradicted, source-granularity, unverified, quoted, missing capture, hedged and unrelated cases; preserve two-source ordering and no raw evidence leaks.
- Add a **seventh** hosted workflow, network disabled without explicit `--live` and pinned to exact approved URLs. Existing six workouts remain unchanged.
- Accept only after complete backend suite, all 7 feature-head workflows, merge, and 7 **new exact SHA main push** workflows including genuine network, source/signal logs and no unsafe support.

## Integrity and limits

A reason tells callers *why this implementation abstained*, **not why the claim is objectively false**. The code `source_grammar_unsupported` does not prove that the source supports a correct date, or that the source can be ignored; it means the parser requires stronger context. Fixed code strings may be trusted as bounded policy explanations but not as independently human-reviewed factual labels. Changes do not add LLMs, semantic NLI, ML training, Hugging Face, arbitrary web search, user agents, production hosting, or human-labeled population accuracy.

Step 232's corpus remains **developer-authored** and its real sources are only Python.org and IANA. This diagnostic milestone improves integration usability and future benchmark error analysis; reliable human-labeled semantic validation remains required.

**Separate non-negotiable external deployment/release gate [#242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242) remains OPEN.** No claim of a customer-facing HTTPS deployment.

## Completion status

**Step 233 ✅ COMPLETE in the explicitly bounded engineering scope**, independently verified through implementation [PR #247](https://github.com/riteshchavan96k/ai-reality-layer/pull/247), merged into `main` SHA `51b27cb90e813c77c916f2223cc7e5b1fdf418f1`.

All **seven** separate hosted `push` workflows completed successfully on that exact merged main SHA. [Python3.13 backend run 38364578347](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38364578347) passed **2,467 tests**; the [new live original-source explanation run 38364578427](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38364578427) passed **12/12 fixed predeclared reason-code outcomes**, including one known safe `source_grammar_unsupported` positive abstention and zero of ten nonpositive cases falsely supported. Five historical genuine-source/HTTP workflows also passed, including the Step 232 12-case policy regression. See [Step 233 scorecard](STEP_233_SCORECARD.md) for exact runs and honesty limitations.

This was **not** an externally deployed user service or general semantic factual correctness evaluation, and was not a trained LLM/ML implementation. A new documentation-only merge must independently pass all seven workflows on its own final main SHA before the *latest* branch is called green. Keep [external deployment gate #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242) OPEN.
