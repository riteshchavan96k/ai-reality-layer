# Step 231 — Scoped Authenticated Pilot Engineering Scorecard

## Exact provenance and revision

The completed previous milestone is **Step 230**, independently green on exact `main` `ec35543095e21c65e85fa2b062d33cbc564642c3` through [PR #240](https://github.com/riteshchavan96k/ai-reality-layer/pull/240).

Step 231's original proposed acceptance included deployment to an **externally reachable HTTPS host**. On 2026-10-13, the project owner explicitly agreed to a **revised engineering acceptance** that permits nonpublic development to proceed without rushing to hosting. This is a deliberate, visible scope change, not retroactive falsification of external-test results. Mandatory actual deployment and operations acceptance is tracked as a **blocking open release item**, [issue #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242).

**Engineering implementation:** merged [PR #241](https://github.com/riteshchavan96k/ai-reality-layer/pull/241), followed by [PR #243](https://github.com/riteshchavan96k/ai-reality-layer/pull/243) fixing a real-container client-side premature-413 socket race. Verified implementation `main` commit **`9e21809cc69fdac1ca998f11b58b1cdf862ed3d0`**. Full exact-head verification and audit records: [PR #243 comment](https://github.com/riteshchavan96k/ai-reality-layer/pull/243#issuecomment-6131687027).

## Independently inspected GitHub Actions main-push results

| Gate | Run | Verified result |
| --- | --- | --- |
| Python 3.13 backend, compile, all history and policy replays | [38301554831](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38301554831) | **2,440 passed in 5.76s**; Step 230 quote examples 3/3 legitimate aligned; 0/7 adversarial incorrectly aligned |
| Genuine original Python.org HTTPS observation | [38301554779](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38301554779) | Success |
| Genuine Python.org + IANA two-publisher HTTPS | [38301554805](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38301554805) | Success |
| Genuine original-source bounded affirmative/negated claim | [38301554933](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38301554933) | Success |
| Actual local Docker HTTP socket and real original Python.org DNS/TLS/HTTPS | [38301554927](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38301554927) | Success: no/wrong bearer **401**; oversized **declared Content-Length** **413**; affirmative `supported`, negative `uncertain`, **not publicly deployed** |

Each is an actual completed successful `push` run with `head_sha=9e21809cc69fdac1ca998f11b58b1cdf862ed3d0`. The original feature PR also passed all five checks on `7436c065ec63a469d576180a66a56d6502383ed2`; the follow-up fix PR passed all five on `81c8609ad7625f3871424e054f9151e14d196b9a`. This was **not** only a synthetic internal function test.

## Failure disclosure and technical boundaries

The first merged-main Step 231 container check [38301265483](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38301265483) **failed**: early valid HTTP 413 can terminate the socket while a naive test client is still uploading a 4 MiB body, causing `BrokenPipeError` before observing the response. The follow-up workflow sends an intentionally over-limit **Content-Length declaration without transferring the body**, verifying the early server refusal through a real socket. **Actual streamed-byte enforcement** has its own application regression test with body bytes. Neither result should be mislabeled as full hostile-network security evaluation.

The pilot requires explicit startup `ARL_RUNTIME_MODE=pilot`, a high-entropy backend-only bearer token and operator-owned JSON array of exact HTTPS source URLs; the provided Dockerfile sets pilot mode. **Development mode is unauthenticated and must never be exposed.** The Docker container is non-root and reproducibly exercised on a GitHub-hosted runner bound to loopback. It has **no independently deployed TLS ingress**, external secret manager or assured throttling; do not expose it directly to the public Internet.

Real original-publisher HTTPS proves observed content on two fixed websites and limited statements; it does **not** prove cryptographic source authorship, all-purpose semantic entailment, objective truth, publisher endorsement or general factual reliability. The 2,440 tests measure the repository's contracts and curated cases, not a representative real-world population. Current retrieval remains constrained to approved URLs and limited atomic grammar.

## Status

**Step 231 ✅ — deployable and authenticated engineering integration completed on the exactly verified merged-main implementation commit.**

**External-hosted customer pilot / production release ❌ NOT DONE**, tracked as [mandatory release blocker #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242). Continue building usable AI Reality Layer functionality nonpublicly; verify hosting security, user behavior, reliability and human-labeled claims before any public/customer release.

This document is a status-only change. Any subsequent documentation-only PR must also pass all five workflows on its own exact final merged-main SHA; record new run IDs in the PR closure comment rather than modifying another unverified commit.
