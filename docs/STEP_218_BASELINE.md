# Step 218 — Measured Official-Source-Anchored Quality Baseline

## What was actually evaluated

**Status: observed and reproducible publisher-anchored adversarial replay.**

Eight factual historical software-release dates were manually checked
against official publisher pages from Python.org, Node.js, Go,
Rust, and Kubernetes. The accompanying statements are **short
reviewer-authored paraphrases**, not verbatim publisher captures.
All source URLs are in `backend/evaluation_fixtures/step218_official_anchored_v1.json`
and enumerated in `docs/STEP_218.md`.

Each source anchor has six offline scenarios: relevant official summary,
attacker-authored contrary content under the same genuine URL,
real but irrelevant official source, an explicitly synthetic conflicting
source, stale simulated observation time, and no freshness policy.

**Limits:** no independent second human annotator, no archived raw source
HTML or content hashes, no authenticated evidence-content provenance,
and no runtime access to live publisher sites. Observation timestamps
are fixed **simulation** values, not actual capture times. These 48
tests evaluate failure modes grounded in real historical facts but
**do not establish field factual accuracy** or measured deployed quality.

## Recorded execution and test reproducibility

First completed hosted Python 3.13 workflow at
[run 37989769535](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/37989769535)
on the feature branch, SHA
`baf156d059f11ba1b573e8acdd0ef222ac7b0834`:

- Full backend compilation: successful.
- Full pytest: **2,034 passed**.
- Unchanged Step 217 fictional benchmark: executed successfully.
- New Step 218 official-source anchored replay: **48 evaluated**.
- Hosted summary captured without modifying quality expectations in
  `docs/STEP_218_BASELINE.json`.
- A subsequent regression
  `test_committed_official_source_scorecard_matches_actual_product_replay`
  requires the committed scorecard to equal a fresh product replay.
  It must pass before the final branch/merge verification.

## Actual results

| Metric | Counts | Result |
| --- | --- | --- |
| Historical-release/source-relevant inputs structurally supported | 8 / 8 | **100%** |
| Explicit synthetic negation conflicts detected | 8 / 8 | **100%** |
| Safe abstention among cases requiring it | 24 / 40 | **60%** |
| **False structural support on abstention-required cases** | **16 / 40** | **40%** |
| **Irrelevant genuine official evidence wrongly supported** | **8 / 8** | **100%** |

### Scenario-by-scenario

| Test scenario | Count | Incorrectly `supported` |
| --- | ---: | ---: |
| Real publisher relevant historical fact | 8 | 0 |
| **Altered content under real publisher URL** | 8 | **8** |
| **Wrong-topic real official source** | 8 | **8** |
| Conflicting explicitly synthetic report | 8 | 0 |
| Stale simulated source observation | 8 | 0 |
| Missing declared freshness policy | 8 | 0 |
| **Total** | **48** | **16 of 40 requiring abstention** |

## Detailed failure analysis

### Critical finding A — Authentic URL does not authenticate document bytes

The test replaces a historical-release summary with
`Not <reviewer-authored release fact>` **without changing the official
publisher URL**. The forged sentence is created by the adversarial
fixture builder; no publisher made that statement.

All eight cases still produce structural `supported` under an
explicit age policy because the current system validates the shape
of the URL and connects the *submitted* claim with that URL; it
**does not check whether the URL actually contains the supplied text**.

This is a genuine distinction between source *attribution supplied by
a developer* and source-*content verification*. Do not claim this has
been solved simply because provenance identifiers are hashed.

### Critical finding B — Official documents unrelated to the question

For the second adversarial family, the input question asks for release
A, but a real publisher's historical release notice about version B
is supplied instead. Both the source URL and reviewer-authored fact
are genuine *for B*, yet none answer the user's question about A.

Again the existing Reality State reports `supported` in **all eight**
cases. This demonstrates that current source-link coverage and freshness
signals are **not a query-to-evidence relevance or entailment test**.

The next design must distinguish:

- *Was any source supplied?*
- *Does the submitted source actually contain the quoted claim?*
- *Does that source support the claim relevant to the **task**?*
- *Has the claim been independently corroborated?*

These are different dimensions; treating one as proof of the others
overstates the system's assurance.

### Existing defenses that held on this corpus

Eight exact-negation synthetic contradictions led to uncertainty.
Eight deliberately old observation timestamps did not pass the
freshness window, and eight cases without explicit age policy
remained uncertain. Eight relevant publisher-anchored factual summaries
received structural support as the narrow oracle expected.

**None** of those outcomes alone measures how the system would handle
new live evidence, hostile pages, ambiguous natural-language queries,
changing internet sources, or false positives for semantic entailment.

## Follow-on engineering decision

**Prioritize separate source-content and task-relevance assurance**:
`source-reported` is a useful but lower assurance level than
`content-checked`, `task-relevant` or `independently corroborated`.
Design the confidence gate so a valid URL plus any fresh text cannot
by itself imply factual or question-relevant `supported`.

Before changing public semantics, add independently collected and
reviewed official-page **actual source excerpts** or licensed
content snapshots, with capture hashes, precise capture times and
blinded reviewers. Use a held-out corpus for evaluating both false
support and legitimate support rates to avoid solving failure cases by
always abstaining.

Do not choose Hugging Face/LLM/model approaches without measured gains
in relevance/entailment and conservative uncertainty on unseen data.
The current tests and scorecard make failure visible; they do not
represent deployed AI Reality Layer as factually reliable.

## Commands

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --output /tmp/step218-full.json
```

The machine-readable artifact
`docs/STEP_218_BASELINE.json` is taken from the hosted CI output,
not manually estimated or upgraded to a passing score.
