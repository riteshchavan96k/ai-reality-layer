# Step 217 — Observed Controlled Reality State Quality Baseline

**Status:** First reproducible 48-case **controlled-simulation quality baseline measured**; these are **not field/world factual accuracy results**.

## Evidence and reproducibility

- Dataset: `backend/evaluation_fixtures/step217_controlled_v1.json`
- Runner: `backend/app/evaluation/reality_state_quality_benchmark.py`
- Recorded machine-readable scorecard: `docs/STEP_217_BASELINE.json`
- First fully successful Python 3.13 GitHub-hosted feature CI: [run 37983616718](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/37983616718), at feature head `55156e492b7682d20be45acc2f8894e561e31d75`.
- CI result: backend compilation succeeded, **2,011 tests passed**, and the quality benchmark printed the actual results.
- The benchmark tests now additionally require the committed JSON scorecard to exactly equal a fresh replay. Re-runs after recording must also pass before merge.

Every service, URL, statement, and oracle world-state is a fictional controlled fixture. No real publisher, public release announcement or live incident was independently consulted. `fixtures.example.test` is intentionally non-real. The dataset's independent simulated oracle is kept out of product input, allowing us to *detect* failure to abstain but not to claim general real-world accuracy.

## Actual observed aggregate metrics

| Measure | Raw numerator/denominator | Observed |
| --- | ---: | ---: |
| Exact candidate claim precision | 64 / 64 | **100%** |
| Exact candidate claim recall | 64 / 64 | **100%** |
| Claim/source pair precision | 68 / 68 | **100%** |
| Claim/source pair recall | 68 / 68 | **100%** |
| Candidate conflict precision | 8 / 8 | **100%** |
| Candidate conflict recall | 8 / 16 | **50%** |
| Candidate conflict F1 | — | **66.7%** |
| **False structural support** on cases requiring abstention | **16 / 40** | **40%** |
| Correct conservative abstention | 24 / 40 | 60% |
| Structural support on oracle-consistent inputs | 8 / 8 | 100% |

**Do not interpret the 100% claim/source numbers as factual truth or entailment**. The labels intentionally describe exact, directly submitted sentences and their documented provenance. These are narrow extraction/attribution measurements on a small controlled distribution.

### Scenario-level failure breakdown

| Case family | Cases | Candidate conflicts correctly identified | Wrongly `supported` |
| --- | ---: | ---: | ---: |
| Recent oracle-consistent reports | 8 | n/a | 0 |
| Sole false submitted source | 8 | n/a | **8** |
| Exact leading-negation source disagreement | 8 | 8 / 8 | 0 |
| Old source observation | 8 | n/a | 0 |
| **Paraphrased semantic disagreement** | 8 | **0 / 8** | **8** |
| Missing freshness policy | 8 | n/a | 0 |
| **Total** | **48** | **8 / 16** | **16 / 40 high-risk cases** |

## Failure analysis — actual actionable defects and limitations

### Priority 1: Semantic disagreement is invisible to the deterministic detector

For example, the controlled test presents these two differently sourced statements:

- `Cedar Search is operational.`
- `Users cannot access Cedar Search at present.`

The gold oracle labels this as a conflict requiring abstention. The existing `ClaimConflictDetector` recognizes only `not/no/never` at the **start** of a text claim, so it detects **0 of the eight paraphrased conflicts**. Since both source claims have canonical links, recent provider/caller-reported observation times and no *detected* conflict, all eight test snapshots become `supported`.

This is measured evidence for assessing an independently evaluated **semantic contradiction / entailment component** or a conservative confidence gate. It does **not** yet justify trusting an LLM's statements without validation.

### Priority 2: A single false source can produce structural support

In eight other controlled cases, the simulated independent world oracle states a positive fact while the only submitted source explicitly claims its negation. The system receives **only the false statement**, a plausible fictional URI, and a recent observation time; its existing structural validation, claim/source linking and freshness checks pass, and the result becomes `supported`.

**It is impossible to prove the hidden reference-world fact from the sole contradictory report itself**. This is a missing independent corroboration/verification capability, not an arithmetic or source ID bug. A fix must not fabricate knowledge of the true world. Candidate strategies include refusing factual-sounding support without independent corroboration and differentiating *reported by a source* from *verified by independent evidence*. Such changes require compatibility design and separate, measured acceptance criteria.

### What worked on this constrained corpus

- Exact source-bound claim extraction and deduplication matched all 64 manually labeled candidate claims.
- All 68 claim-to-reported-source pairs matched the oracle annotations.
- Eight leading-negation conflicts were detected.
- Eight stale-source cases abstained appropriately, as did eight missing-freshness-policy cases.
- Eight controlled supported cases retained expected structural support.

These cases do not cover real publication authentication, evolving source content, news retrieval, incomplete fragments, adversarial prompt injection, untrusted web formats, non-English sources, large-scale latency, or statistically representative real user queries.

## Product decision

**Do not mark the AI Reality Layer product factually reliable yet.** A **40% false-support rate on the 40 controlled cases requiring abstention** misses the aspirational zero-false-support high-risk evaluation target.

The immediate follow-on work should begin with:

1. **External real-source evaluation:** collect a small set of permitted, dated, immutable original-source captures from official software-release/status channels. Retain provenance, exact capture time, usage terms and human-reviewed gold labels. Include an annotator-blinded assessment so the author of the model output is not the author of the reference answer. Do not present fictional URLs as actual evidence.
2. **Distinguish assurance levels:** design a non-misleading distinction between `source-reported`, `cross-source corroborated`, and `independently verified` before promoting evidence to a truth-sounding `supported` claim. Test with false reports and misleading corroboration.
3. **Evaluate semantic contradictions:** compare conservative rules, small well-scoped language models and optional model adapters using the fixed benchmark plus a *separate* unseen, independently labeled holdout. Measure both recall **and** false-positive disagreements, latency and inference cost.
4. **Repeat baseline and compare**: do not change gold oracle labels to flatter the algorithm. Version datasets and metrics; retain negative results.

This is a practical direction, **not** a fabricated assertion that Steps 218+ have been specified or implemented.

## Benchmark completion is distinct from model/product success

The milestone succeeds when there is an independently annotated *controlled*
corpus, an honest metrics runner on the existing production pipeline, dataset
integrity and leakage tests, a committed observed scorecard, and successful
hosted branch/merged-main/final-sync CI. The product target—low error rates
under real-world evidence, calibrated uncertainty and developer value—remains
**unverified and unsatisfied** by this benchmark.

Run the baseline:

```bash
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.reality_state_quality_benchmark --output /tmp/step217-replay.json
```

The JSON result includes individual scored failure entries in full mode; the
tracked `STEP_217_BASELINE.json` is the exact hosted `--summary-only`
output, not hand-estimated percentages.
