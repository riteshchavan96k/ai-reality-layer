# Step 223 — Server-Observed Source Freshness Integrity

## Why this follows Step 222

[Step 222](STEP_222.md) established a genuine operator-allowlisted HTTPS
publisher capture and auditable `capture_observed_at`. Yet, in the
`POST /api/v1/reality-state/evidence` **strict** path, freshness evaluation
continued to use the **client-provided** `documents[].observed_at`.
The capture metadata was available only under independent text assurance,
not in the canonical `source_observation` or `freshness` results.

This is a real trust-boundary error: with independently captured text, a
client-controlled timestamp could make an old server capture appear fresh,
or a fresh server capture appear stale. The source text can be real while
the source *observation age* is misleading.

## Behavior and explicit boundary

- For strict `require_independent_source_text_match: true`, when a backend
  observer returns a **matched, well-formed** capture timestamp, it replaces
  the caller's reported observation time as the authoritative timestamp in
  the canonical observation/freshness signals for the corresponding URI.
- This observation's `observation_method` is
  `independent_source_capture`. The source/provenance linkage, hashing,
  strict excerpt comparisons and absence of publisher authentication claims
  are unchanged.
- In strict mode the caller MAY omit `observed_at` even with an explicit
  freshness policy. If a trusted capture is missing and the client also
  supplies no valid reported observation, the observation/freshness result
  becomes **unavailable** and support is **uncertain** (fail closed).
- Invalid/future capture times cannot silently fall back to a client's
  reported time to claim support.
- Legacy backend-injected reader callbacks that provide no capture metadata
  continue to use the caller-reported observation time when it is supplied.
  This preserves the Step 220 synthetic evaluation, but **does not** turn
  those readers into independently time-authenticated sources. Production
  Step 221/222 HTTPS reader returns capture metadata when successful.
- The non-strict API and direct calls preserve their existing requirements
  and behavior; an explicit freshness window without observed-at remains
  invalid there.

A source's capture time is simply **when our backend observed its response**.
It is NOT the time the publisher originally published the content, the
time an underlying claim became true, or the freshness of the world fact.

## Implementation

- `backend/app/reality/independent_capture_freshness.py`:
  exact-URI/source-ID mapping and captured timestamp use; fail-closed
  on missing or invalid authoritative observations.
- `backend/app/reality/source_observation.py`:
  explicit `independent_source_capture` method in the validated canonical
  observation type.
- `backend/app/orchestrator/orchestrator.py`:
  applies backend capture precedence before calling the existing freshness
  evaluator and confidence aggregation.
- `backend/app/api/evidence_reality_state.py` and
  `backend/app/reality/submitted_evidence.py`:
  strict-mode optional submitted observation date, guarded at runtime.
- `backend/tests/test_step223.py`: positive and adversarial real pipeline
  and in-process FastAPI tests, with **fake independent-reader transport**.
- `backend/app/evaluation/capture_freshness_benchmark.py`:
  five independently specified, deliberately *synthetic* timestamp scenarios
  with asserted expected outcomes; included in the standard Python 3.13
  `Backend tests` CI workflow. This is not a live publisher benchmark.
- The existing `.github/workflows/step222-live-source-smoke.yml` remains
  the actual live HTTPS/TLS publisher canary, now strengthened to submit a
  deliberately old **2024 client observation timestamp** for the authentic
  page excerpt and require canonical observation provenance to equal the
  independent **current HTTPS capture timestamp**. The forged same-URL
  rejection test remains unchanged and must continue passing.

## Five-scenario synthetic replay acceptance

| Controlled case | Expected Reality State | Expected timestamp provenance |
|---|---|---|
| Fresh server capture, stale client report | `supported` | independent capture |
| Stale server capture, fresh client report | `uncertain` | independent capture |
| Fresh server capture, no client report | `supported` | independent capture |
| No capture and no client report | `uncertain` | unavailable |
| Legacy reader without capture, client report | `supported` | client-reported; **not independently captured** |

These outcomes test trust-source precedence and safe abstention, not
semantic meaning, original publication age, calibration, or historical fact
accuracy. Passing five synthetic cases does NOT imply a general false-support
rate of zero.

## Reproduction

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.independent_source_assurance_benchmark
python -m backend.app.evaluation.capture_freshness_benchmark
```

Continue to require a successful unmodified Step 222 real HTTPS canary on
the same commit. Do not disable its TLS/DNS/allowlist controls for CI.

## Security and honesty limits

A properly configured, backend-owned HTTPS reader provides the observation
time, not the client. An arbitrary backend-injected simulated reader can
still lie; this is not cryptographic timestamping or an immutable archive.
A compromised server, publisher, DNS/TLS environment or attacker-controlled
page can still yield false content. CSS-hidden text, misleading quoted
passages, entities and semantic contradiction remain outside this step.
The feature does not solve independent factual truth or source publication
timestamps.

## Final evidence

Step 223 engineering changes merged via [PR #222](https://github.com/riteshchavan96k/ai-reality-layer/pull/222).

- Final feature head `d2dd5062840c31f53edcb552fce2faed7a58878d`: [full backend CI 38082233411](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38082233411) passed compilation, **2,207 tests**, historical 217/218/220 replays and all **5/5** synthetic Step 223 timestamp-spoof scenarios; [genuine HTTPS CI 38082233402](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38082233402) passed and required a current server capture to override the 2024 caller timestamp for the original publisher page.
- Independent merged-`main` SHA `6305f95d3821750b6de2e3850df600da7b5e0511`: [backend CI 38082301186](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38082301186) passed **2,207 tests** and all four benchmark workflows; [live HTTPS CI 38082301189](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38082301189) succeeded.
- The final documentation-only status synchronization commit must itself pass BOTH hosted workflows on its exact `main` SHA before reporting that Step 223 is complete on current `main`.

These results demonstrate a narrowly scoped, tested **source-observation-time trust correction**, not evidence of world-fact accuracy or publisher-signed timestamps.
