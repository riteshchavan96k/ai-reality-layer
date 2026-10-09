# Step 221 — Secure Operator-Allowlisted HTTPS Original-Source Reader

## Why this step follows Step 220

Step 220 built an opt-in strict source-text comparison boundary but had
**no actual HTTPS reader configured**. Therefore normal strict-mode requests
could only abstain. Step 221 supplies a genuine server-owned HTTPS
retriever restricted to exact operator-approved URLs. This addresses a
real functionality gap without claiming source truth or publisher endorsement.

## Server-only configuration

Set an environment variable on the **backend**, not in the API request:

```bash
export ARL_INDEPENDENT_SOURCE_ALLOWED_URLS='["https://www.python.org/downloads/release/python-3130/"]'
```

This must be a JSON array containing 1–20 unique, full HTTPS URLs. Without
the setting the backend continues to use an unconfigured strict-mode
reader and returns `uncertain`. Invalid JSON, unsafe URLs and invalid
allowlist sizes cause configuration errors, not an unsafe fallback.
Exact URL matching means even different paths or queries are not allowed.

On the existing `POST /api/v1/reality-state/evidence` endpoint use
`require_independent_source_text_match: true` and provide source
`uri`, an **exact excerpt** from the source's visible text, and
normal task/entity/freshness inputs. The excerpt must actually appear
in the fetched and parsed document. An arbitrary summary or an unrelated
source document is not sufficient.

## Actual network and data processing

1. Reject unsafe URI shapes, IP-literal/local-looking names, non-HTTPS
   schemes, credentials, fragments, unusual ports and control characters.
2. Resolve the domain **once**; reject empty/mixed/public-and-private DNS
   replies and non-global IP addresses. Connect using the approved IP,
   while retaining the original hostname for standard TLS SNI,
   certificate chain and hostname checks.
3. Make an HTTPS GET directly (no implicit proxy use) and **do not follow
   redirects**. Require HTTP 200. Enforce a maximum 5-second connection/
   socket timeout; default body limit is **256,000 bytes**.
4. Accept only UTF-8-compatible `text/html` or `text/plain` responses
   with identity encoding. Reject unsupported charsets/content types,
   oversized, incomplete or invalid response bodies. HTML extraction
   drops scripts, styles, SVG and head metadata; the strict matching
   check operates on resulting visible text, not original markup.
5. The server's retrieved **raw response bytes** are SHA256-hashed. A
   separate SHA256 identifies the rendered comparison text, and the
   server records a UTC capture timestamp. Successful per-source
   strict evidence metadata exposes `capture_sha256`,
   `capture_observed_at`, and the previously existing
   `observer_content_sha256`.
6. The *entire submitted excerpt* must match each observed source. All
   sources must match for the strict assurance gate. Any failure remains
   `uncertain`, independently of other confidence, entity or
   freshness checks.

## Implemented files

- `backend/app/reality/allowlisted_https_source_reader.py` — HTTPS
  retrieval with exact operator allowlist, public-IP DNS checks, pinned
  TLS, no redirects, bounded decode and visible HTML extraction.
- `backend/app/orchestrator/dependencies.py` — optional server-only
  environment configuration; default remains fully disabled.
- `backend/app/reality/independent_source_text_assurance.py` — records
  validated byte digest and UTC source observation timestamp for
  successful strict source checks.
- `backend/tests/test_step221.py` — real reader exercised using
  controlled fake transports, DNS/socket/TLS spies, bad responses and
  end-to-end Reality State construction; no live internet required.
- Existing Step 217–220 benchmarks continue unchanged.

## Critical honesty/security boundaries

These safeguards are defense-in-depth **not a formal SSRF/security
certification**. Production operators must additionally enforce secure
egress and DNS/proxy policy, maintain trusted CA stores, rate limits,
monitoring, abuse controls, and carefully curate the exact URL allowlist.
A network-observed document can itself publish something false; text
presence is not fact verification, semantic support or independent
corroboration. The backend does NOT cryptographically establish
publisher authorship or archive immutable original publisher pages.

The stored SHA256 is a digest of bytes seen by the reader, not a
publisher signature. Capture time is when our server observed the
response, not when the publisher last updated it. Original raw HTML
is NOT persisted. Pages requiring scripts, redirects, authentication,
PDF extraction, compressed bodies or large responses are intentionally
unsupported and will fail closed.

The hosted regressions use a fake HTTPS transport to test behavior,
including IP pinning and TLS context configuration, **not a real live
publisher TLS transaction**. An operator-reviewed and permitted live
source smoke test remains necessary before operational deployment.
No new ML/LLM model, knowledge graph, fact-checker, or semantic inference
is claimed.

## Completion evidence

Completion requires full Python 3.13 compilation, all pytest tests,
unchanged Step 217/218/220 benchmark runs, passing feature-branch CI,
successful PR merge, independent merged-main CI and final status-sync
commit CI matching the exact current `main` HEAD. Only then mark the
scoped engineering work ✅.

## Reproduce

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.independent_source_assurance_benchmark
```
