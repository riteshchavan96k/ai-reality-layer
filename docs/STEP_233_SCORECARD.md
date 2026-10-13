# Step 233 — Strict Original-Source Claim Decision Reasons: Engineering Scorecard

## Verified provenance and newly defined scope

The independently completed predecessor was Step 232 at exact merged `main` SHA `65c604bb64a5c8b83529aaaee2de1b5995b13425` with six passing workflows and 2,457 backend tests. No prior Step 233 document or agreed pre-existing Step 233 description existed, so the scope was explicitly defined **before implementation** from the documented Step 232 deficiency: a genuine release-date question appropriately abstained but reported only `insufficient`, leaving downstream AI developers unable to distinguish incomplete observation, unsupported grammar, and unrelated atomic assertions.

**Step 233 does not attempt to make an unscoped date label prove a subject-specific release date.** Instead it adds bounded reason codes for all original-source alignment decisions, preserving existing support/abstention behavior and source verification.

## Implemented changes

- [Implementation PR #247](https://github.com/riteshchavan96k/ai-reality-layer/pull/247) adds per-source `decision_reasons` to `evidence.claim_alignment`, source-ref paired with a **fixed, bounded policy code** only; existing `source_decisions` and overall `status` are unchanged.
- Reasons distinguish bounded alignment, contradiction, claim/source grammar unsupported, unrelated atomic assertions, missing independent original-source observation, inadequate evidence context, quotation, counterstatement and missing capture integrity metadata. No source HTML, token, external error text, or user content is interpolated into reasons.
- `backend/tests/test_step233.py` tests the new behavior with controlled fake source-reader contracts (not presented as original publisher evidence).
- The Step 232 runner now checks reason/source IDs, emits reason codes in its digest-only audit and **retains the original immutable Step 232 fixture and all 12 existing policy expectations**.
- New `backend/app/evaluation/step233_source_reason_live_smoke.py` and `.github/workflows/step233-live-decision-reasons.yml` run the 12 predeclared explanation cases using **actual original Python.org and IANA DNS/IP-checked HTTPS/TLS and the strict FastAPI API**. Default CLI denies network without an explicit `--live` opt-in; fixed URL allowlist only.

## Independently inspected merged-main engineering proof

[PR #247](https://github.com/riteshchavan96k/ai-reality-layer/pull/247) merged into exact `main` **`51b27cb90e813c77c916f2223cc7e5b1fdf418f1`**. All seven **separate GitHub-hosted `push` workflow runs** completed with `conclusion=success` and matching exact `head_sha`:

| Workflow | Exact merged-main run | Independently verified |
| --- | --- | --- |
| Backend Python 3.13, full historical regressions | [38364578347](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38364578347) | **2,467 tests passed in 4.55s**; Step 230 quote-origin replay still 0 wrongly aligned |
| New Step 233 real TLS / twelve-case reasons | [38364578427](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38364578427) | **12/12 expected reason codes**; no false support among 10 nonpositive fixed cases |
| Existing Step 232 original-source safety | [38364578334](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38364578334) | **0/10 falsely supported; 1/2 developer-labeled positives supported, 1 abstained** |
| Real authenticated Docker pilot HTTP | [38364578494](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38364578494) | Success, no public hosting |
| Real Python.org HTTPS | [38364578490](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38364578490) | Success |
| Real Python.org+IANA HTTPS | [38364578355](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38364578355) | Success |
| Real bounded claim source alignment | [38364578361](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38364578361) | Success |

The known reference-positive release-date case remains `insufficient`, now with **`source_grammar_unsupported`**. This is not semantic entailment or truth verification. No test has been relabeled from abstained to supported to make the benchmark look better.

## Truthfulness and limitations

These are **developer-labeled, fixed** scenarios drawn from just **two original publisher websites**. The 12/12 explanation-code match and zero false supports on ten adversarial cases are engineering policy checks, NOT independent human-label population accuracy, unbiased precision/recall, field dependability, publisher endorsement or verified universal fact accuracy. A fixed reason code explains the **system's own gate**, not the objective truth of the underlying claim or webpage.

No real hosted LLM, ML, deep-learning, Hugging Face, vector search or multi-agent integration was added. This milestone makes the deterministic verification system more interpretable and enables measuring future semantic-model proposals. Human-labeled broader data and contextual inference remain future product gaps.

The separately mandatory external HTTPS/customer deployment and operations release gate **[#242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242) remains OPEN**. The actual real TLS checks above used controlled GitHub-hosted CI, not customer-facing deployment.

## Acceptance status

**Step 233 ✅ COMPLETE within its scoped engineering functionality** on the independently verified merged implementation commit. This documentation-only status synchronization should be merged with all seven new exact-main push workflows green; its precise final commit/run IDs should be recorded as a PR audit comment, without creating another unverified main commit.
