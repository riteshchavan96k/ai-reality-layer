# Step 232 — Original-Source Claim-Safety Engineering Scorecard

## Provenance / why Step 232 was selected

Predecessor **Step 231** was independently complete under its explicitly limited engineering scope at `main` `d2acf37f526a60bdfb4731947beb17f082379ccb` with 2,440 tests and 5/5 workflows. There was **no pre-existing Step 232 description or numbered roadmap file** in the repository; [Step 232's acceptance and rationale](STEP_232.md) were established on a reviewed branch from the documented remaining trust-evaluation gap, not claimed as a recovered historical step.

The original-source strict API checked a few narrow, fixed official publisher claims, but had no separate versioned challenge gate enumerating false-support and known safe abstention cases. A real ML/LLM model integration must be judged against a reproducible baseline.

## New work and reproducibility

- [PR #245](https://github.com/riteshchavan96k/ai-reality-layer/pull/245): 12 predeclared cases with fixed labels and exact original-source URL IDs, covering two genuine TLS publisher sites (Python.org and IANA).
- `backend/evaluation_fixtures/step232_original_source_claim_v1.json`: versioned IDs and explicit **developer-authored, not independently reviewed** labels. The manifest may not silently drop cases or relabel positives.
- `backend/app/evaluation/step232_source_claim_safety.py`: fixed allowlist required, network disabled without `--live`, pre-observed digest/time receipts plus **actual strict FastAPI API requests** that separately retrieve the original HTTPS source. Stops on an unexpected supported adversarial case, broken source audit, claimed factual truth, mismatched scoped attribution or changed alignment.
- `backend/tests/test_step232.py`: validates fixture tampering, false support, source-identity swap, missing capture metadata, false publisher/semantic truth claims and default network prohibition.
- `.github/workflows/step232-source-claim-safety.yml`: sixth, independent hosted genuine-source workflow with digest-only audit artifact and no credential/publisher HTML leak.

## Independent first merged-main engineering acceptance

[PR #245](https://github.com/riteshchavan96k/ai-reality-layer/pull/245) merged to **`main` `06307e533ea44e5d0ac76a93c0641b6f584a1001`**. All **six** workflows were independently re-fetched and checked: `event=push`, exact matching `head_sha`, `status=completed`, `conclusion=success`.

| Gate | Actual new main push run | Verified outcome |
| --- | --- | --- |
| Python 3.13 backend and all historic evaluation replays | [38362081385](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38362081385) | **2,457 tests passed** in 7.73s; Step 230 quotation policy regression retained |
| Step 232 original-source fixed adversarial safety challenge | [38362081256](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38362081256) | **12/12 policy conformant**; 2 developer-labeled positive claims, **1 supported / 1 abstained**; **0 of 10 nonpositive cases falsely supported** |
| Authenticated real Docker HTTP and Python.org TLS | [38362081358](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38362081358) | Success, no public deployment |
| Original Python.org HTTPS | [38362081352](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38362081352) | Success |
| Original Python.org + IANA two-publisher HTTPS | [38362081287](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38362081287) | Success |
| Original bounded claim Python.org HTTPS | [38362081244](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38362081244) | Success |

The first feature-head backend run **failed one newly authored test assertion**: the test rejected the harmless word `excerpt` appearing inside the public *scenario label*, instead of checking whether raw evidence fields were leaked. That assertion was corrected without altering product source verification. Full tests and all six workflows were then successful on the revised feature head `ac2fc2f3476a08102a42bafef384fdfebaba4823`. No runtime authority or source policy was weakened. The failure is preserved in GitHub history.

## Honest limits and next evaluation work

**This is a policy conformance / engineering safety benchmark, NOT a factual reliability estimate.** The cases are authored by the project developer/assistant rather than sampled or independently human-labeled; both originals are from the same two previously allowed publishers; linguistic grammar remains narrow; a correct release-date claim demonstrates a known *abstention* where the user wants richer intelligence. Never present 0/10 as unbiased population precision, 1/2 as an accuracy rate, or passing CI as certification of semantic entailment.

A future evaluation must involve independent human review and more varied original publishers, languages, time changes and document formats; only then compare a real LLM, neural NLI, embeddings and related advanced technology against this deterministic baseline. The new step does NOT install or serve any LLM, train an ML model, integrate Hugging Face, deploy publicly, or establish source publisher cryptographic authentication.

**Step 232 ✅ scoped engineering completion:** based on six successful original-source/HTTP and backend workflows on the exact merged implementation main. Final documentation-only scorecard sync needs six independently verified new CI runs on its own final main SHA; record those run IDs in its PR audit comment without introducing an extra unverified main commit.

The **separately mandatory external HTTPS/customer deployment gate [#242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242)** remains OPEN and is not affected by Step 232.
