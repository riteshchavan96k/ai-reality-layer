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

**Pending** final feature-head backend/full benchmark + both real HTTPS
workflows, independent merged-main reruns, and final documentation sync
verified on its exact final main SHA. Mark complete only after all these
checks genuinely pass.
