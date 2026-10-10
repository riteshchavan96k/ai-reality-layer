# Step 222 — Real Publisher HTTPS Observation and End-to-End Quality Smoke

## Verified motivation and narrow scope

Step 221 implemented a real operator-allowlisted, DNS-pinned HTTPS reader, but
its 2,175-test suite used mock network transports and never proved that the
unmodified reader could fetch an actual publisher site in GitHub-hosted Python
3.13 and drive the public Reality State API through strict source assurance.

Step 222 is a **live historical publisher canary**, NOT production source
authorship verification, semantic entailment, population-level factual quality
evaluation, source archiving, or deployment approval.

## Operator allowlist / security

- The fixed and independently reviewed original source is
  `https://www.python.org/downloads/release/python-3130/`.
- Operators *explicitly* enable the reader with the existing backend
  `ARL_INDEPENDENT_SOURCE_ALLOWED_URLS` JSON array, containing **only this URL**.
- The tool has **no arbitrary URL parameter**, runs with no network by default,
  and requires an explicit `--live` flag.
- The source reader enforces URL equality, global-only DNS results, pinned
  TCP, TLS certificate + hostname verification, redirect denial, no proxy,
  a five-second socket timeout, a 256 KB bound on both wire bytes and decoded
  bytes, and UTF-8 HTML/plain-text restrictions. Do not interpret this as formally audited SSRF safety.
- The published CI workflow has no tokens/secrets or user-provided endpoint,
  and emits only validation decisions, capture UTC times and digests.
- Step 222 adds strictly bounded **single-member gzip decoding** because the
  real publisher response used compressed transfer encoding despite the
  client's `Accept-Encoding: identity`. Deflate, Brotli, concatenated gzip,
  invalid checksum, truncated data, decoded size amplification beyond the
  bound, and other encodings remain fail-closed. Source SHA256 is computed
  over the original on-wire response body, not decompressed text.
- Original publisher HTML/text is **not stored**, and returned errors never
  print raw body or backend transport credentials.

## Distinct independent oracles

The test uses **declared-before-capture**, human-reviewed page content, not
literal text copied back from a successful observation. It checks:

1. Direct live HTTPS response contains *two independently predeclared*
   historical publication anchors. Return URI, raw response SHA256, and UTC
   capture time must be valid and recent.
2. The real FastAPI `POST /api/v1/reality-state/evidence` strict-mode path
   accepts the operator-reviewed visible-text excerpt as **structurally
   supported**, with source capture audit recorded and both
   `publisher_authenticated` and `semantic_support_verified` false.
3. The **same official publisher URL** with a fixed forged 1900 release date
   must produce `uncertain` and the expected
   `submitted_text_not_in_observed_content` audit reason. A forged source
   must not inherit a successful capture digest.
4. All tests retain the disabled-default network path and refuse broader
   or incorrect server allowlists. Mocked tests verify failure paths, while
   the separate live GitHub-hosted workflow really performs DNS/socket/TLS.

There are **two scored API scenarios and three independent HTTPS reads**.
Even 2/2 desired classifications is **not** a statistical accuracy estimate;
this is an integration smoke and source-text anti-forgery demonstration.

## Reproduction

For local/operator use, only after deciding the fixed page is approved:

```bash
export ARL_INDEPENDENT_SOURCE_ALLOWED_URLS='["https://www.python.org/downloads/release/python-3130/"]'
python -m backend.app.evaluation.live_source_quality_smoke --live
```

For an auditable output without storing source text:

```bash
python -m backend.app.evaluation.live_source_quality_smoke --live --output step222-live-audit.json
```

Without `--live` or the exact operator allowlist, networking must be refused.
The live workflow is `.github/workflows/step222-live-source-smoke.yml`. Its
uploaded JSON digest-only artifact is retained for 30 days. Network loss,
publisher redirects, page changes, and strict content-limit mismatches
intentionally fail closed. No retry/re-bypass is automatically enabled.

Repeat hosted full Python 3.13 compilation, pytest suite and historical
Step 217/218/220 replay checks via the separate `Backend tests` workflow.

## Acceptance and limitations

Engineering completion requires green full-regression and real-live publisher
smoke workflows on feature branch and merged `main`, plus current exact main
SHA verification. Do not infer publisher cryptographic authentication or
historical fact truth from TLS/byte digests. A release page may be old, false,
updated, CSS-hidden, dynamic, too large, compressed or intermittently
unreachable. The reader does not retain raw captures. This narrow task does
NOT deliver production-scale original-source archiving, independently blinded
human factual annotation, multi-publisher generalization, or live deployment.

## Hosted evidence

Feature-branch SHA `9e9b0ac051553e5f93adbcd673a2d5347364a6e4` passed:
- [Python 3.13 backend CI 38079874619](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38079874619): **2,191 tests passed**, compile successful, Step 217/218/220 replays passed.
- [Real HTTPS publisher canary CI 38079874635](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38079874635): real DNS/TLS/GET and strict FastAPI request path succeeded, **1/1 legitimate excerpt structurally supported; 0/1 forged excerpt supported**; digest-only artifact `step222-live-https-audit` uploaded with 30-day retention. Original wire-body SHA256 and observation time visible in restricted CI log/artifact; no HTML archived. Earlier live canary runs failed closed because the publisher sent compressed content until bounded gzip support was implemented. No weakening of URI allowlisting, TLS, redirects or output bounds was necessary.

These are **one-publisher, two-scenario observations**; no real-world population error rate is estimated. Reconfirm final-feature-head and independently merged-main workflows after completing these documentation changes. Do not claim successful live retrieval from mocked tests or web search alone.
