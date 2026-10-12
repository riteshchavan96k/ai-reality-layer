# Step 231 — Authenticated Deployable Original-Source Pilot (in progress)

## Why this follows verified Step 230

Step 230 was first independently closed at main `3a9889a9c0ac7ebe39597f7f71b8bd57b4991d21`
(PR #238), and its remaining scorecard/status reconciliation merged via
[PR #240](https://github.com/riteshchavan96k/ai-reality-layer/pull/240) at
`ec35543095e21c65e85fa2b062d33cbc564642c3`.
The four original workflows passed on the **latter exact final main SHA**, with
**2,414 Python tests passing**. This branch must not overwrite the updated
Step 230 source of truth. The pipeline already has a working,
allowlisted, SSRF-conscious original-publisher HTTPS reader and opt-in bounded
claim alignment, but the actual FastAPI POST endpoints had **no caller
authentication** and the repository had **no deployable runtime image**.
Additional synthetic claim grammar would not close either product gap.

This step introduces a reviewable authenticated single-tenant pilot runtime and
a reproducible container. Its purpose is a real HTTP boundary with real
original-source HTTPS, not yet an internet-facing production launch.

## New runtime behavior

- Default **development** mode preserves historical API behavior and tests.
  It is **not safe to expose development mode to the Internet**.
- Set backend-only ARL_RUNTIME_MODE=pilot and ARL_PILOT_BEARER_TOKEN to enable
  bearer authentication for **every route except GET /health** (all other
  methods on /health are not business endpoints). Token must be 32–256 printable,
  non-whitespace ASCII bytes. Generate it from a cryptographically secure
  random generator, never from a human phrase.
- Pilot additionally requires the server-owned
  ARL_INDEPENDENT_SOURCE_ALLOWED_URLS exact HTTPS URL list. The existing
  source reader validates the list; clients cannot modify it.
- No token, wrong token, duplicate Authorization fields, malformed scheme
  or oversized credential: **401**, WWW-Authenticate: Bearer, no business work
  or original-source network fetch. Unauthorized requests are checked before
  request-body validation. API responses are non-cacheable in pilot mode.
- Invalid pilot configuration: **503** with no secret details; the container
  preflight exits nonzero instead of launching. A configured token without
  explicitly selecting pilot mode is also rejected (not silently ignored).
- Pilot application middleware also caps **actual inbound HTTP body bytes at 4 MiB** after authorization (HTTP **413** for excess), including uploads without reliable Content-Length. This is defense-in-depth and **does not replace** ingress request size limits or rate controls. The operator URL allowlist must be a JSON **array**, never an object or string.
- The existing X-Request-ID correlation header still accompanies denials.
  The credential is never copied into the Reality State or recorded by the
  new middleware. The container turns off Uvicorn access logging.

This adds **access control**, not user identity management, per-tenant scopes,
JWT, OAuth, billing, rate limiting, a threat-model certification or publisher
authentication. A bearer credential conveys full pilot access while valid;
operators must keep the token private and rotate it if compromised.

## Reproducible restricted local runtime

Run in the repository root with Docker installed:

```bash
docker build -t ai-reality-layer-pilot .
export ARL_PILOT_BEARER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(40))')"
export ARL_INDEPENDENT_SOURCE_ALLOWED_URLS='["https://www.python.org/downloads/release/python-3130/"]'
docker run --rm --read-only --tmpfs /tmp:rw,noexec,nosuid,size=8m \
  -p 127.0.0.1:8080:8080 \
  -e ARL_PILOT_BEARER_TOKEN \
  -e ARL_INDEPENDENT_SOURCE_ALLOWED_URLS \
  ai-reality-layer-pilot
```

The published host port is bound to loopback. The image is non-root, with
one application worker and no source write paths. The container refuses to
start without a valid token and source allowlist. To call a protected route,
set Authorization: Bearer <token> over the local loopback connection. The
same container can be used behind a **separately controlled HTTPS ingress**,
but never expose container port 8080 directly over public HTTP.

The token is passed from the shell's environment by name to avoid putting its
literal value in the Docker command arguments. In real hosting, store it in the
platform's secret manager and restrict operator access. Do not place keys in
GitHub, CI logs, requests sent to anyone else, support tickets or screenshots.

## CI acceptance / source-backed validation

The Step 231 workflow builds the actual image, verifies it refuses to start
without a token, runs it as a read-only container on a GitHub-hosted runner,
then sends real localhost HTTP requests:

1. GET /health without a token must return healthy.
2. POST without or with a wrong token must return HTTP 401.
3. POST with a random bearer token and a fixed, approved Python.org original
   release-page excerpt must invoke the real DNS/TLS/HTTPS reader and produce
   an affirmative bounded claim alignment (not a synthetic fake).
4. The opposite claim from the same verified source must be refused
   conservatively. Capture byte SHA-256, backend capture UTC timestamp and
   HTML quote-scope clearance must be present on positive source assurance.
5. No raw source HTML or token is printed in the smoke report.
6. Full Python 3.13 suite, historical evaluation replays and all previous
   genuine original-source workflows remain green on exact PR head.

Backend/tests/test_step231.py checks request-level authorization, malformed
and duplicate headers, oversized authenticated and unauthenticated payloads, malformed JSON allowlist shape, configuration refusal, unchanged dev-mode contract and
existing strict Reality State integration with a **fake network**. The CI
container smoke is a **separate genuine network check**; neither alone
establishes production deployment security.

## Still required for a genuinely deployed, customer-usable pilot

- Select and configure an actual hosting account, domain and HTTPS ingress.
  No cloud credentials or live deployment exist in this repository; GitHub
  Actions executes an ephemeral CI container only.
- Enforce TLS, maximum request-body size, per-client ingress rate limiting,
  egress allowlisting for port 443, secrets storage/rotation, health monitoring,
  alerting, incident procedures, request logging without raw evidence or tokens,
  cost budgets and abuse prevention.
- Verify the real deployed **external HTTPS URL** independently: unauthenticated
  denial, authenticated positive and negative original-source requests,
  observation/capture audit, uptime, response latency and operational failure
  modes. Use external test credentials and never publish them.
- Run a varied, independently human-labeled publisher/claim evaluation before
  calling the system factually dependable. The current fixed release-page
  assertions are an engineering canary, not representative factual accuracy.
- Consider source readability, user-facing selection of official URLs,
  explanation quality and operator feedback after the narrow pilot works.

## Acceptance status

**NOT COMPLETE.** The initial code/CI workflow is a candidate implementation.
A Step 231 completion checkmark requires a reviewed merged PR, all mandated
tests and hosted workflows on the exact merged main SHA, **and a genuine
externally reachable authenticated HTTPS pilot with the deployment and
security controls above verified**. Do not mark the milestone complete based
on synthetic tests or GitHub's ephemeral localhost Docker job alone.
