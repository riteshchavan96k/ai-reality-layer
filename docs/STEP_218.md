# Step 218 — Official-Publisher-Anchored Reality State Quality Evaluation

## Identification after Step 217

Step 217 completed the first **controlled fictional** 48-case benchmark:
the system returned structurally `supported` in **16/40 (40%)** cases
requiring abstention and detected **8/16 (50%)** conflicts. Those scores
were deliberately not represented as field accuracy.

The next product-relevant question is whether the same Reality State
processing behaves correctly with evidence **anchored to actual
publisher statements**, and what happens when a developer submits a
false document under an official URL or a genuine document unrelated
to the task.

Therefore Step 218 introduces **official-source-anchored historical
release evaluation** before modifying confidence logic, adding an LLM,
or claiming live factual verification.

## Sources reviewed

On October 10, 2026 (IST), public first-party release pages were
inspected for eight historical release dates:

| Publisher | Historical release | Date | Official page |
| --- | --- | --- | --- |
| Python.org | Python 3.13.0 | 2024-10-07 | https://www.python.org/downloads/release/python-3130/ |
| Python.org | Python 3.12.0 | 2023-10-02 | https://www.python.org/downloads/release/python-3120/ |
| Node.js | Node.js 24.0.0 | 2025-05-06 | https://nodejs.org/en/blog/release/v24.0.0 |
| Node.js | Node.js 22.0.0 | 2024-04-24 | https://nodejs.org/en/blog/release/v22.0.0 |
| Go | Go 1.24 | 2025-02-11 | https://go.dev/blog/go1.24 |
| Go | Go 1.25 | 2025-08-12 | https://go.dev/blog/go1.25 |
| Rust | Rust 1.85.0 | 2025-02-20 | https://blog.rust-lang.org/2025/02/20/Rust-1.85.0.html |
| Kubernetes | Kubernetes v1.34 | 2025-08-27 | https://kubernetes.io/blog/2025/08/27/kubernetes-v1-34-release/ |

Only short **newly authored factual release-date summaries** are stored
in the fixture, not verbatim text from the publishers. Their URLs and
historical dates were manually checked from the linked pages.

**Critical limitations:** There are NO immutable raw-page captures,
content hashes of publisher responses, external independent human
annotations, blinded second review, or demonstrated live retrieval.
The assistant's source check should not be mistaken for an external
audit. Page contents and URLs may change after source review.

## Dataset and six experiments per release

`backend/evaluation_fixtures/step218_official_anchored_v1.json`
contains eight anchors and **48 labeled scenarios**:

1. **Relevant publisher-backed summary:** one date fact corresponding
   to the official release notice. This is the only case family labeled
   as safe to structurally support within the *narrow dated historical
   fact task*.
2. **Official-URL content forgery:** attacker-authored
   `Not <release fact>` is submitted while **reusing the real
   publisher URL**. The statement is **NOT** an official claim, and
   `uri` equality does not authenticate the supplied bytes. Oracle
   requires abstention.
3. **Wrong-topic but genuine official page:** user asks about
   release A, while the submitted statement and URL are from a
   different real official release page B. Source validity alone must
   not imply task relevance.
4. **Explicit synthetic contradiction:** a second source whose
   `fixtures.example.test` URI and title explicitly mark it
   synthetic asserts `Not <release fact>` against the official
   paraphrase. The conflict should be detected conservatively.
5. **Stale replay timestamp:** the publisher-anchored statement is
   supplied with a controlled 5.5-hour-old observation and a one-hour
   allowed age. This is a simulated timestamp condition, **not** a
   historical claim about when the publisher page was really fetched.
6. **Missing freshness policy:** with no declared maximum age,
   the system must not infer reliable freshness merely because a
   caller supplies an observation timestamp.

For deterministic comparisons, the fixed **synthetic** replay time is
`2026-10-09T18:30:00Z`. The controlled observation times are
`18:00Z` (recent) and `13:00Z` (old). They are **simulation
inputs, not measured collection times** or publisher publication dates.

The independent reviewer oracle `should_abstain` and other label
metadata stay completely outside the public API request.

## What is implemented

- `backend/app/evaluation/official_source_quality_benchmark.py` —
  validates sources and annotations, builds the six scenarios per
  release, invokes the existing evidence Reality State builder with
  injected deterministic clocks, validates public Pydantic request
  and response contracts, and reports per-case, per-scenario and
  aggregate results.
- `backend/tests/test_step218.py` — full corpus coverage,
  challenge construction, mismatch labels, fake-source markers,
  malicious URL/content association, time-bound behavior, gold
  exclusion, malformed fixture rejection, zero-network replay,
  and truthful metric calculation.
- Existing `.github/workflows/backend-tests.yml` runs both the
  unchanged Step 217 benchmark and the new Step 218 benchmark after
  full Python 3.13 compilation and pytest.
- `docs/STEP_218_BASELINE.json` and
  `docs/STEP_218_BASELINE.md` preserve **actual observed CI
  results only**, after the first successful run. A parity test
  can then prevent stale scorecards.

## Metrics and scoring

The new scorecard measures:

- **False-support rate** among the 40 cases labeled
  `should_abstain=true`.
- **Safe abstention rate** on those cases.
- Correct structural support among eight relevant official-publisher
  paraphrase cases.
- **Wrong-topic evidence false-support rate** among eight cases
  where the available source is from another genuine official release.
- Detection rate for eight deliberately explicit synthetic
  contradiction cases.
- Per-case source URLs, prediction status, scenario and uncertainty
  indicators; no independent publisher-content authentication claim.

A passing regression suite means the scores are **reproducible**,
not that the quality scores themselves satisfy real-world standards.

## Reproduction

From repo root:

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --output /tmp/step218-cases.json
```

The evaluator makes **no** outgoing HTTP requests at run time; it
cannot prove that currently hosted page content matches the locally
authored summary or reject forged documents simply by checking a URL.

## Acceptance and next decisions

For this engineering milestone to be completed:
- The original Step 217 benchmark must remain unchanged and passing.
- Publisher pages must be linked, facts historically attributable,
  and tampered/irrelevant content explicitly marked as controlled
  interventions.
- The runner must evaluate 48 cases without leaking oracle labels,
  audit false `supported` behavior, and refuse malformed datasets.
- The actual observed baseline must be committed, with negative
  outcomes preserved.
- Backend Python 3.13 compile, **all** pytest cases and both
  benchmark replays must succeed on the feature head, merged main,
  and final status-sync commit.

For **real-world product accuracy**, this is only a next increment.
The subsequent phase still needs immutable permitted actual source
captures, multiple independently blinded human reviews, direct
source-content authenticity checks, varied real-world queries,
and evaluation against unseen data.

The true decision point after Step 218 is whether first to prevent
**wrong-topic official sources** and **URL-content spoofing**
from triggering misleading support, with carefully designed assurance
labels that do not conflate `source-reported` with
`independently verified`.

Do not introduce a heavyweight LLM/model before measuring the
solution against held-out real-source evidence.
