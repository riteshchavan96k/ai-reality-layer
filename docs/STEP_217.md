# Step 217 — Reality State Ground-Truth Quality Baseline

## Why this is the correct next engineering action

The Step 216 repository has **1,992 passing regression tests** but no
claim-level factual quality benchmark. The existing
`backend/app/evaluation/benchmark.py` explicitly measures
orchestration/structural execution, **not evidence truth, claim
attribution, or false-support behavior**.

The production `EvidenceQualityValidator` checks source/content shape,
`ClaimEvidenceLinker` checks reported source attribution, and
`RealityConfidenceSignalAggregator` uses coverage, reported observation
freshness and exact-negation candidate conflicts. A self-consistent,
recently observed *false source report* can therefore cause a
`status="supported"` without authenticated evidence of factual truth.

This milestone introduces an **independent and reproducible quality
measurement**, not a speculative new model or an assertion that all
product-quality targets are already met.

## Deliverables

- `backend/evaluation_fixtures/step217_controlled_v1.json`: 48
  independently labeled controlled scenarios across eight fictional
  software services (six cases per service).
- `backend/app/evaluation/reality_state_quality_benchmark.py`: offline
  evaluator that invokes the **existing developer-submitted evidence
  production pipeline**, validates both public request and response
  Pydantic models, and compares resulting Reality States with labels
  that are never passed into the product.
- `backend/tests/test_step217.py`: replay, dataset validation,
  independent-label tests, fail-loud invalid input, honest metric
  accounting, and actual FastAPI handler compatibility checks (without HTTP transport).
- The existing backend GitHub Actions workflow now prints a
  `--summary-only` quality report on each successful backend build.
  Quality failures appear as scored results; **CI does not conceal them
  or change product confidence policy to make scores look better**.
- `docs/STEP_217_BASELINE.md`: actual observed results and next decision
  (filled only after successfully running the evaluator).

## The corpus — explicit controlled simulation, NOT real-source evidence

**Crucial honesty boundary:** Every source name, source document,
`fixtures.example.test` URI, and reference-world state in this
first corpus is fabricated on purpose. They are controlled fixtures,
**not** independently authenticated official software release notices
or a field sample of live-world factual accuracy. The label
`world_reference_is_simulated: true` is mandatory for every case;
the runner refuses cases that omit it.

This is appropriate for *first isolating and measuring system behaviors*
without mixing them with live retrieval/provider problems. It is NOT
completion of the larger real-source, independently human-annotated
evaluation requirement, which remains a separate next-phase gate.

Each service contains six specifically annotated scenarios:

1. **Consistent reported truth:** a claim agrees with the hypothetical
   oracle, with a recent timestamp and an explicit age policy. Four
   cases include duplicate source coverage to test deduplicated
   lineage; these are *different* source URIs.
2. **False sole report:** the controlled oracle says the positive
   reference claim is true, but the sole submitted source says
   `Not <positive claim>`. There is no independent truthful source
   available to the system. This intentionally tests overconfidence:
   **source attribution alone cannot establish truth**.
3. **Explicit negation from two sources:** the candidate positive
   claim and its `Not` counterpart appear from distinct sources.
4. **Stale observation:** a positive claim with an observation from
   08:00 UTC is assessed at 12:30 UTC against a 3,600-second window.
5. **Paraphrased disagreement:** two sources make semantically opposing
   claims that are **not** an exact leading `not/no/never` pair. The
   controlled label demands disagreement/abstention but the current
   deterministic detector is not expected to fully recognize it.
6. **No freshness policy:** a recent observation is present but no
   maximum-age policy is declared. The system should retain unknown
   freshness and not promote this to proof of current truth.

The evaluation time is a fixed `2026-01-01T12:30:00Z`, and all
source observation values are at or before that time. No network
activity, API keys, live provider or machine clock dependency is needed
to reproduce the measured quality signals.

## Separation of labels from predictions

The evaluator builds each real API request from only:

- `task`, `entity`, `documents`, and `freshness_max_age_seconds`.

The independent `gold` object is kept in the fixture file but never
fed to a production component, model, confidence calculation or HTTP
API input. Tests actively verify that hiding, changing an oracle label,
or changing expected claim text **changes scores but not product
predictions**.

`gold.should_abstain` is a **controlled safety oracle**, not an
unqualified factual truth label. For example, a single misleading
report must be treated cautiously by a hypothetical independent
fact-verifier even though the current API has no way to know it is false
from the sole supplied document. Thus the measured false-support rate
reflects our target **product behavior**, not an ability that the
current input should be assumed to provide.

## Evaluation metrics — micro counts, no invented probabilities

- Candidate claim precision/recall/F1 using case-insensitive,
  whitespace-canonicalized text matches to gold labels.
- Claim-to-source precision/recall/F1 based on exact
  `(claim identity, source URI)` pairs (not textual entailment).
- Candidate conflict precision/recall/F1 based on unordered gold
  claim-pair identities.
- **False support rate**:
  `cases with gold.should_abstain and output.status == "supported"`
  divided by all `gold.should_abstain` cases.
- **Safe abstention rate**: cases requiring abstention whose status is
  not `supported` divided by all such cases.
- Correct support rate on eight controlled oracle-approved cases.
- Separate counts for each of the six scenarios, plus full per-case
  reports when not using `--summary-only`.

All metrics are transparent sample proportions. Zero denominators
return `null`. No claim of calibrated model probabilities, statistical
population representativeness or live-world accuracy is made.

### Reproduction

From the repository root, with
`backend/requirements-dev.txt` installed:

```bash
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.reality_state_quality_benchmark --output /tmp/step217-full.json
python -m pytest backend/tests/test_step217.py -q
python -m compileall -q backend/app
python -m pytest
```

The first command prints the summary including critical overconfidence
failures; the second writes a full case-level JSON audit trail. GitHub
CI runs the summary after full pytest.

### Quality acceptance — measurement integrity versus product success

**Step completion** requires:

1. A fixed corpus covering at least 40 cases and all six categories,
   labeled separately from product inputs.
2. Run-time validation that fails loudly on duplicate cases,
   corrupted annotations, invalid source refs or pretending a fixture
   has independently verified real-world truth.
3. The same deterministic pipeline that the developer-submitted API
   uses, including source timestamps, confidence policy, claim
   extraction/linking and conflict detection.
4. Metrics computed from raw counts, with explicit scenario and
   case-level errors. A high false-support rate is **not hidden**.
5. A committed baseline report containing observed counts, real
   limitations and an actionable next product engineering decision.
6. Full Python 3.13 GitHub-hosted compile + pytest on the branch,
   independently on merged main, and on the final status-sync commit.

**Product success is a different gate**. On future blind
independently human-reviewed real-source evaluation, aspire to zero
false-supported high-risk cases and quantify actual uncertainty and
error intervals. That gate is not satisfied by Step 217's synthetic
simulated-oracle corpus, even if all regression tests pass.

## Scope discipline

No change to the production Reality State algorithm or public APIs,
no new LLM/ML/Hugging Face inference, no auth or deployment assertion,
no source credibility certification, no real-world search or external
requests. The previous orchestration benchmark is not overwritten.

The purpose is to decide, based on visible failure data, whether the
highest-leverage next work is authenticating evidence, entailment
validation, semantic contradictions, retrieval, or temporal history.
