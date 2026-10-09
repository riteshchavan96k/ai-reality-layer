# Step 219 — Observed Post-Gate Quality Scorecard

## Audit trail

**Measured feature-branch execution:** [GitHub Actions run 37996925741](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/37996925741), feature SHA `0c22178af4e69f74d21d321307b4b34aba6ba68f`, Python 3.13 backend compiled and **2,071 automated tests passed** before the current-scorecard parity regression was added. Both pre-existing Step 217 and Step 218 benchmark runners also executed successfully.

The complete machine-readable **actual hosted-run output** for both 48-case benchmarks is recorded in `docs/STEP_219_SCORECARD.json`. A Step 219 regression now requires its `current` scores to agree with fresh product-pipeline replay on both data sets. The final feature head, independent merged main, and status-sync SHA must all pass these tests before marking Step 219 complete.

**Historical preservation:** `docs/STEP_217_BASELINE.json` and `docs/STEP_218_BASELINE.json` were intentionally NOT rewritten. They remain the original **before** scores. Baseline parity regression tests in these prior test files were changed to check immutable historical results; Step 219 owns the live scorecard parity checks.

## Measured before and after

| Metric | Historical | Step 219 | Scope |
| --- | ---: | ---: | --- |
| Step 218 wrong-topic official evidence **wrongly supported** | **8/8 (100%)** | **0/8 (0%)** | Explicit full entity not found in any linked claim |
| Step 218 false `supported` on cases requiring abstention | 16/40 (40%) | **8/40 (20%)** | Other failures remain |
| Step 218 correctly structurally supported relevant reports | 8/8 | **8/8** | Narrow reviewer-paraphrase dataset |
| Step 218 explicit synthetic contradiction detected | 8/8 | **8/8** | Detector unchanged |
| Step 217 false `supported` among cases requiring abstention | 16/40 (40%) | **12/40 (30%)** | Four paraphrases no longer text-align |
| Step 217 candidate contradiction recall | 8/16 (50%) | **8/16 (50%)** | **No semantic detector improvement** |

### Source-failure breakdown after Step 219

On the 48 official-source-anchored controlled cases:

| Case type | Cases | Incorrectly `supported` after gate |
| --- | ---: | ---: |
| Relevant historical official source paraphrase | 8 | 0 |
| **Forged claim with original publisher URL** | 8 | **8** |
| Different genuine official release than requested | 8 | **0** |
| Exact explicit synthetic contradiction | 8 | 0 |
| Stale simulated observation | 8 | 0 |
| No explicit observation-age policy | 8 | 0 |

The **correct support rate for eight narrow relevant cases remains 8/8**. This does not measure a representative population of legitimate tasks; a strict entity-in-every-linked-claim rule may abstain on many genuinely relevant real documents.

### Step 217 change is not semantic contradiction understanding

In the fictional controlled benchmark, four of eight paraphrased-disagreement cases now abstain because **some linked claims do not repeat the target entity's full literal name**. The detector still recognizes only its original explicit leading negation pairs. The eight gold conflicts in that family are still missed. Do not cite the drop in false `supported` as an improvement in semantic entailment or contradiction accuracy.

### Biggest unresolved security and factual-reliability gap

All eight **synthetically forged source-content** inputs remain `supported` under an otherwise valid official URL because the false text still mentions the requested entity. The system does **not** fetch, authenticate or compare the original publisher content for submitted evidence. Even a perfect textual relevance check cannot rule out malicious or mistaken source assertions.

**`explicit_entity_text_alignment_only` is not evidence authenticity.**

### Next evidence-driven work

A separately scoped future milestone should acquire source contents from trusted provider-side retrieval with safe networking and bounded response processing, capture actual content/URI/time, and distinguish `submitted` from `publisher-observed` evidence with explicit assurance. The API should not upgrade confidence solely on an unauthenticated caller-provided URL/content pair.

The evaluation program must also add actual, permitted original-source captures, blinded independent human-reviewed gold, varying live tasks, and holdout cases (including target coreference and mentions in irrelevant contexts). Optimize false supports **and** false abstentions, not only one metric.

**Do not mark the overall AI Reality Layer product factually reliable at Step 219.** This milestone is a limited, experimentally measured relevance safeguard.

## Commands

From repo root:

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
```
