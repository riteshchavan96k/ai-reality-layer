# Step 226 — Multi-Publisher Real HTTPS Evidence Evaluation

## Identified source-backed gap after Step 225

Steps 221–225 built HTTPS original-source text observation, source-byte audit,
source-observation freshness and conservative HTML quote boundaries. However
the only **genuine hosted network** quality check was a *single* historical
release page on `www.python.org`. No one-publisher canary can establish that
the same mechanisms work across independently operated original-source domains,
nor test one malformed/forged document contaminating a mixed-source request.

Step 226 extends the observed scope to two **fixed, separately hosted, official
publisher pages**, with independent, predeclared affirmative and forged test
excerpts. It exercises the real FastAPI public strict Reality State route and
retains all previous DNS/TLS/HTTP, freshness and parser acceptance gates.
The result is a small **real-network engineering quality scorecard**, NOT
an unbiased field-factual-accuracy measurement.

## The two reviewed, exact-URL source targets

1. Python Software Foundation historical 3.13.0 original release page:
   `https://www.python.org/downloads/release/python-3130/`.
   Positive quotation: `This is the stable release of Python 3.13.0`.
   A distinct historical date phrase must also be observed independently.
2. IANA official reserved-domain reference:
   `https://www.iana.org/domains/reserved`.
   Positive excerpt: `a number of domains such as example.com and example.org`.
   Separately check both the page heading and
   `are maintained for documentation purposes.` as source context.
   These are **separate anchors**: Step 225's structural quote boundaries
   intentionally prevent reconstructing their larger surrounding passage
   into one artificial continuous quote. The wording was adjusted only
   after an actual live capture demonstrated the structural separation;
   no parser rules, allowlist or expected rejection were weakened.

Each fixed source has a deliberately fabricated text excerpt for its own
exact URL (a fake 1900 Python date and a forged statement that the example
domains can be registered/transferred). Inputs were decided by the reviewer
without copying the live response bytes back into the submitted evidence.

## Fixed scorecard: six real HTTPS/API scenarios

| Fixed API scenario | Expected Reality State | Number of matched sources |
|---|---|---:|
| Python.org actual release excerpt | supported | 1 |
| Python.org false historical excerpt | uncertain | 0 |
| IANA actual named-example excerpt | supported | 1 |
| IANA false registration excerpt | uncertain | 0 |
| Both original-source excerpts correct | supported | 2 |
| Python correct + IANA forged | uncertain | 1 |

**Acceptance:** 3/3 authentic scenarios supported, 0/3 forged scenarios
supported; both original sources individually observed on real HTTPS;
per-source hashes, capture UTC timestamps and strict source refs checked;
positive two-source requests retain accurate source IDs and server-capture
observation timestamps. The mixed forged case must refuse support even if
the other publisher's excerpt is independently observed and fresh.

Source text presence is **not** publisher-signed content, semantic entailment,
claim-level verification or a proof that the underlying statement is true.
There are only TWO pages and SIX predeclared challenges, with no random
sampling, blinded annotations or population error estimates.

## Security and implementation boundaries

- `backend/app/evaluation/multi_publisher_live_smoke.py` has a **hardcoded
  immutable choice** of two exact HTTPS URLs and independent hostnames,
  with **no arbitrary URL argument**. It first refuses all network when
  the operator's existing `ARL_INDEPENDENT_SOURCE_ALLOWED_URLS` JSON list
  is absent, narrower, broader or altered.
- Live execution requires an explicit `--live` flag and the configured
  reader type. The existing HTTPS reader still rejects local/private DNS,
  pins vetted public IPs under certificate/hostname verification, rejects
  redirects, disables proxy use, and bounds socket time, wire/decompressed
  bytes, source media type and parsed text.
- The `POST /api/v1/reality-state/evidence` strict path receives fixed,
  human-reviewed excerpt strings, **not fetched HTML echoed as test data**;
  client observation timestamps are omitted to exercise independently
  backend-captured observation authority from Step 223.
- A documented auditor report contains only source IDs/URLs, SHA256 of
  originally observed HTTP bytes, observation timestamps, source counts,
  source-level statuses, and class labels. No raw publisher HTML, cookies,
  credentials, full provider exceptions or user-provided data is emitted.
- Bad source responses, site changes, DNS restrictions, HTTP errors and
  any oracle mismatch fail closed. **Do not** bypass those protections to
  obtain a green build.
- The specific workflow is
  `.github/workflows/step226-multi-publisher-live.yml`; it runs on push
  and pull requests in a GitHub-hosted Python 3.13 environment, with the two
  explicitly pinned URLs, least-privilege contents-read permissions and
  a digest-and-score-only artifact retained for 30 days.
- The established Step 222 Python.org original-publisher live workflow and
  Python 3.13 complete regressions / historical Step 217–225 quality replays
  must *also* remain green on the same exact SHA.

## Reproduction

After an operator explicitly approves both fixed public publisher targets:

```bash
export ARL_INDEPENDENT_SOURCE_ALLOWED_URLS='["https://www.python.org/downloads/release/python-3130/","https://www.iana.org/domains/reserved"]'
python -m backend.app.evaluation.multi_publisher_live_smoke --live
python -m backend.app.evaluation.multi_publisher_live_smoke --live --output step226-two-publisher-live-audit.json
```

On Windows PowerShell the same variable can be set with
`$env:ARL_INDEPENDENT_SOURCE_ALLOWED_URLS='["https://www.python.org/downloads/release/python-3130/","https://www.iana.org/domains/reserved"]'`.

For hermetic regression, test-only transport fakes must never be reported as
real publisher observation:

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.independent_source_assurance_benchmark
python -m backend.app.evaluation.capture_freshness_benchmark
python -m backend.app.evaluation.html_visibility_quality_benchmark
python -m backend.app.evaluation.structural_quote_benchmark
```

## Remaining gaps toward a real AI Reality Layer product

The limited success does not establish independent historical publication
times, immutable trusted archival, semantic claim entailment, correct
interpretation of quoted/negated language, cryptographic content signatures,
generalization over more domains and document formats, or human-labeled
real-world precision/recall. All require different future milestone evidence
and should not be treated as solved by exact-text assurance.

## Hosted CI evidence and final acceptance

Step 226 source-backed engineering implementation merged through
[PR #228](https://github.com/riteshchavan96k/ai-reality-layer/pull/228).

- Final feature SHA `476200aa8336883aa8a14557f7024b387e083e62`:
  [Python 3.13 backend 38086166054](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38086166054) passed compilation, **2,307 tests**, Steps 217/218/220/223/224/225 replays;
  [original Python.org live run 38086166011](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38086166011) passed;
  [new original Python.org + IANA live run 38086166083](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38086166083) passed two actual independent HTTPS publisher captures and **six API quality cases**.
- Independently merged `main` SHA `a763632002fe3e761cb0179276c35e67e6ed7178`:
  [backend 38086240943](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38086240943) passed **2,307 tests** and every replay;
  [original source HTTPS 38086240972](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38086240972) passed;
  [two-publisher HTTPS 38086240949](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38086240949) passed.
- The **narrow six-case live result** was 3/3 legitimate scenarios classified supported and 0/3 forged scenarios classified supported, including one mixed-document attack refused. Each source was checked against a current DNS/TLS/HTTPS response, source-specific SHA256 and UTC observation audit, with no raw response bytes in the report.
- Earlier attempts failed closed against the original overlong IANA excerpt because the conservative Step 225 HTML reader kept a structural boundary. Final accepted IANA wording is a *shorter actually contiguous original-source excerpt* plus separate contextual anchors; no hidden or cross-block text was stitched.
- Final documentation-only status sync commit must separately pass all **three** CI workflows on the exact resulting current `main` SHA before declaring Step 226 complete.

These measured observations test a small fixed approval scope, **not**
statistically representative field reliability, semantic entailment,
cryptographic publisher authenticity, or real-world factual accuracy.

## Final exact-main-SHA acceptance closure (verified 2026-10-11)

The documentation-only Step 226 closure [PR #229](https://github.com/riteshchavan96k/ai-reality-layer/pull/229) was merged at `cb24105e292c67694f75879fdc9048fa9b41b199` (2026-10-10 21:07:07 UTC). Its **own** three `push` workflow runs have been inspected through GitHub Actions' workflow-run records, job steps and logs (not merely copied from the earlier feature-branch scorecard):

- [Backend tests run 38086389765](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38086389765): `head_sha=cb24105e292c67694f75879fdc9048fa9b41b199`, completed/success; Python 3.13 compilation, all legacy Step 217/218/220/223/224/225 replays and **2,307 tests passed** (`2307 passed in 7.06s`).
- [Original publisher HTTPS run 38086389737](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38086389737): same exact SHA, completed/success; real approved Python.org HTTPS capture and positive/forged API canary plus audit upload succeeded.
- [Two-publisher HTTPS run 38086389744](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38086389744): same exact SHA, completed/success; Python.org and IANA real HTTPS captures, six strict API cases, audit upload; job log confirms **3/3 authentic supported, 0/3 forged supported and 3 conservative refusals**.

**Step 226 narrowly scoped engineering milestone is complete on that exact reviewed main SHA.** This audit record does not certify any later commit automatically; any new `main` SHA needs its own status checks before it is called green. The fixed source texts and two publisher sites are not a field-validity or semantic-entailment study, and they do not justify production factual-reliability claims. No Step 227 change is included.
