# Step 234 — Restricted External HTTPS Pilot Deployment and Independent Acceptance (IN PROGRESS)

## Verified predecessor, scope and status

The latest verified completed milestone is **Step 233**: the exact final `main` SHA before this work was `729456ed3e4ef57be598f28fe40885e01d6846df`, from merged [PR #248](https://github.com/riteshchavan96k/ai-reality-layer/pull/248), with **seven successful exact-SHA push workflows** and **2,467 Python backend tests**. The fixed Step 232 original-source safety evaluation is developer-labeled and does NOT demonstrate general factual accuracy. There was no previous `docs/STEP_234.md`.

This Step 234 scope follows the verified *product* blocker, [mandatory external deployment/operations issue #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242), not an invented previously agreed roadmap number. The restricted Step 231 Docker pilot is **not remotely deployed**; Step 233 CI fetches real publisher HTTPS from hosted runners but does NOT serve the API over public HTTPS.

**Completion criterion:** an operator-authorized, restricted, externally accessible HTTPS pilot with independently confirmed TLS, authorization, source evidence, limits, operational controls, and a real external client integration. Do **not** label Step 234 complete based only on this PR, local Docker, staged documentation or GitHub Actions. Keep Step 233 as the last completed step and issue #242 OPEN until independently tested release acceptance.

## Completed preparatory engineering in this branch

- `backend/app/evaluation/step234_external_https_pilot.py`: standalone Python-standard-library independent **remote** HTTPS verifier, deliberately requiring `--live`, an explicit approved HTTPS origin, and a separate environment-provided bearer credential. It must be executed from a machine **outside** the deployment's hosting infrastructure after the operator approves the target.
- Refuses IP literals, local/non-global DNS, arbitrary methods or paths, nonstandard ports, URL userinfo/query/path, proxies and HTTP redirects. It resolves and pins a globally routable address before certificate-chain/hostname-verified TLS. The verifier never fetches arbitrary source URLs from the client side, sends the token to another origin, or prints response bodies, tokens or raw publisher evidence.
- Checks seven bounded API behaviors: health; absent-token 401; wrong-token 401; early authenticated declared 4 MiB+1 refusal (413); authenticated genuine allowlisted Python.org claim alignment with source receipt and bounded reason; matching claim negation refusal; and an out-of-allowlist source that may never become supported.
- `backend/tests/test_step234.py`: offline tests for DNS and origin refusal, route allowlist, no implicit network, missing or malformed credentials, strict response expectations and false-success refusal. These use an injected *fake transport* and **do not** prove a deployed endpoint.
- **No new production listener, public exposure, cost commitment, external cloud account, secret, token rotation, inbound operational controls, semantic AI claim, or new factual accuracy label.** Earlier source reader, API semantics, Step 233 suite and historical workflows are preserved.

## Restricted external deployment — pending operator authorization

The repository does not contain a hosting account, domain ownership, authorized budget or existing external HTTPS pilot. Deploy only after the operator supplies and approves these. Do not generate or publish cloud credentials, submit billing details, or expose the development backend publicly.

1. Choose an owned hosting service, an **access-restricted staging environment**, cost ceilings, source-egress policy, DNS hostname and managed TLS certificate. Record environment owner and permitted callers in a private release record.
2. Use the existing Step 231 non-root container only in `ARL_RUNTIME_MODE=pilot` behind a separately managed reverse proxy/HTTPS ingress. Do not publicly expose port 8080 or use plain HTTP for clients. Apply network segmentation and restrict egress to approved HTTPS source destinations; retain the backend's exact original-source allowlist, DNS/IP and TLS checks as defense in depth.
3. Configure `ARL_PILOT_BEARER_TOKEN` with a newly generated unpredictable secret **in the hosting provider's secret manager**, never in GitHub, plaintext scripts, command histories or PRs. Limit secret-read permissions. Test replacement and revocation safely.
4. Configure `ARL_INDEPENDENT_SOURCE_ALLOWED_URLS` on the server as a JSON array containing **only reviewed publisher URLs**. The supplied verifier expects `https://www.python.org/downloads/release/python-3130/` to be allowlisted. No client-supplied URL becomes an authority.
5. Enforce **ingress** authentication/rate and concurrency limits, 4 MiB max body size, timeouts, TLS 443-only, non-root execution, read-only root FS, capped CPU/memory/disk, deployment rollback, dependency/image review, minimal privacy-conscious logging, monitoring, alerting and cost quotas. The application middleware alone is NOT enough. Plan source-license and retention handling.
6. From a **separate independently operated computer/network** after approval, load a valid pilot token directly into the `ARL_STEP234_PROBE_BEARER_TOKEN` environment variable using the operator's secret-management practice. Run:

```bash
python -m backend.app.evaluation.step234_external_https_pilot \
  --endpoint https://approved-pilot.example.org --live
```

The hostname above is an illustrative placeholder, **not a real deployed endpoint**. Do not paste the real token into commands, chat, logs or CI output. The tool's output reports only check identifiers and booleans; success is *one bounded acceptance input*, not evidence of all operational requirements.

7. Independently inspect TLS certificate/hostname, direct HTTP port reachability, expiry/renewal, ingress rate limiting, invalid/private source redirects, timeout and source drift, secret rotation, monitoring alerts, incident response, availability, remote latency and restricted pilot billing. Validate a minimal actual downstream AI client uses the endpoint safely, refuses unsupported claims, and does not receive authoritative factual assurances from uncertain evidence.
8. Retain **redacted** external test timestamps, exact tested Git SHA/image digest, domain ownership evidence, observer network provenance, status results, cost and operations readiness, and an independent human-reviewed original-source challenge set. Keep secrets and raw evidence OUT of PR comments/logs.

## Mandatory evidence before completion checkmark

- [ ] Hosting account, cost, domain, environment and network controls explicitly authorized.
- [ ] Nonpublic staged service actually deployed behind audited TLS ingress; direct port 8080 inaccessible.
- [ ] Managed secret storage plus proven revocation/rotation, public 401 and 413 and ingress policy controls.
- [ ] External independent-client `--live` probe successful against actual endpoint (not ephemeral GitHub localhost HTTP).
- [ ] Source-change, redirect, DNS, retry/timeout and rate-control failure modes tested.
- [ ] Monitoring, privacy-conscious logs, rollback, workload limits and realistic remote latency evidence recorded.
- [ ] Small real downstream AI client tested; varied independently human-labeled original-source evaluation conducted before factual reliability is advertised.
- [ ] All project regression tests and **seven new exact-final-main-SHA workflows** passing after any merge.
- [ ] #242 independently reviewed and closed only after genuine release acceptance.

## Explicit limitations

- An external DNS name and TLS certificate alone do not prove publisher authorship, factual truth, operating security or readiness.
- The checker intentionally covers only one fixed Python.org affirmative, one negation and limited API denials; a changing publisher page may force appropriate abstention. Its seven passing checks would be a **smoke test**, not a representative accuracy or penetration test.
- The standalone verifier does not validate the operator's cloud resources, domain ownership, secret hygiene, direct HTTP port closure, ingress rate limits, independent observer location or latency/availability. Those require documented independent operational verification.
- No hosted ML/LLM, general contextual inference or human-labeled population quality evaluation was added here.
- **Status: Step 234 pending external deployment; Step 233 remains the last completed milestone.**
