# Step 235 — Fail-closed downstream AI claim decision gate

## Repository-derived scope and predecessor

At this step's start, verified `main` was `ecfeaf75efd2cb1f0af0f44e6eb30c463373be92`: 2,515 backend tests and eight successful independent exact-SHA push workflows, including the original Python.org claim-only live API canary. The **last fully completed pre-existing numbered milestone was Step 233**. Step 234's external HTTPS deployment acceptance remains **deferred and unfinished**, [release gate #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242) stays open. The project owner explicitly directed us to keep building core functionality now and deploy **after core project completion**. No historical Step 235 specification was found. This Step 235 scope is transparently derived from the proven next product gap, **safe consumption by another AI application of the new claim-only Reality State**.

## Product value

An AI application's grounding layer must not treat an API HTTP 200, the word "supported", a client-chosen URL, a publisher excerpt, or a missing nested field as authoritative on its own. Deliver a small **Python client adapter** that calls the existing `POST /api/v1/reality-state/claim` once, validates the request-bound result and relevant independent-source provenance, and returns one restricted decision:

- `bounded_supported` / `may_use_as_bounded_evidence=true`: only for one exact independently observed, unique, unquoted, fresh, atomically aligned assertion, with all existing Reality State policy gates met.
- `bounded_contradicted` / `may_use_as_bounded_evidence=false`: only a bounded source-level opposing atomic assertion; **not universal proof the claim is false**.
- `abstain` / `may_use_as_bounded_evidence=false`: all failures, uncertain/insufficient/unavailable or incomplete/mismatched/replayed responses.

### Acceptance criteria

1. Keep the existing strict claim API and source allowlist behavior. Add a non-secret **request-binding SHA-256** computed by the backend from canonical validated claim/entity/exact source/freshness; include it in every claim endpoint response. This is an anti-mix-up identifier, **not authentication, a signature, a publisher attestation or evidence of truth**.
2. Client makes one deliberate call to an injected trusted API transport using a caller-provided pilot bearer credential; it does not select network origins, discover arbitrary publishers or access the network on import. The operator/application owns TLS, secret storage and transport. No token or raw evidence is printed in decisions.
3. Validate response byte-size, HTTP status and JSON object, request binding, exact source and entity identity, canonical Reality State, server verification status, claim alignment status and reason, independent source identity and unique-unit conditions, source capture digest/time, source quote/counterstatement checks, freshness, conflict and confidence guards before allowing *bounded* support.
4. Detect bounded contradiction with the same observed-source and receipt guards. Unknown/stale/mixed/reordered/malformed/forged/unavailable responses must **abstain**, including incorrect SHA, extra source rows, conflicting internal support indicators, missing required fields, future capture times or stale capture times. Never interpret HTTP 200 as acceptance.
5. Prove behavior with unit and actual local authenticated FastAPI integration tests, an **independent actual Python.org HTTPS canary** integrating this client with real `TestClient` API calls, and all preserved historical original-source/Docker workflows on exact GitHub PR and merged-main SHA.
6. Record bounded observed metrics and honest limits. **No new ML/LLM/agent provider, general semantic entailment, independently human-labeled population factual accuracy, or external deployment** is claimed.

## Explicit security boundaries

This client is a conservative downstream *policy consumer*, not a source of independent truth. An attacker controlling the API connection or JSON can forge a SHA-256 request binding; the operator must authenticate the real API and use verified TLS for any external connection after release approval. For now, local `TestClient` demonstrates integration without external deployment. A captured genuine upstream response still cannot prove publisher authorship. Unsupported source grammar should abstain, even if true. No data from a client response is fed into a model or executed automatically.

## Checkpoint

**IN PROGRESS** until the final merged-main exact-SHA suite and new real-source consumer canary independently pass. Step 234 release gate #242 stays open.
