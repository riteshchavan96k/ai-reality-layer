# Step 250 — On-demand authenticated live-to-history Reality State reconciliation

## Verified predecessor and genuine gap

Step249 ✅ was independently accepted on exact final main `1078fa4c553a13f15b8757633c355476a8e6360d` via [PR #278](https://github.com/riteshchavan96k/ai-reality-layer/pull/278). The final-main gate comprised **21/21 successful GitHub Actions** and **3,064 passing Python backend tests**, including real Python.org source history and authenticated read-only historical API. No earlier `docs/STEP_250.md` existed.

Previously, AI apps could separately obtain *historical* evidence through Step249 and a fresh source-cited answer through Step241; the existing API did **not** securely reconcile the fresh source reading against the MAC-validated latest observation of the same timeline in one authorized request. Step250 adds that narrow, real product capability without automatic monitoring or externally deployed infrastructure.

## Actual product operation

The proposed new opt-in **`POST /api/v1/reality-state/timeline/recheck`** accepts the Step249 structure `{ "root_record_id": "<random lower-case 32 hex>", "claim": { "claim_text": "...", "entity": "...", "source_uri": "https://...", "freshness_max_age_seconds": 3600.0 } }`. The claim must match the saved canonical request, including its freshness window. **Requires existing `ARL_RUNTIME_MODE=pilot`, a valid bearer token, an exact source URL in `ARL_INDEPENDENT_SOURCE_ALLOWED_URLS`, and `ARL_TEMPORAL_RECHECK_API_ENABLED=1` (disabled otherwise).** All original Step247/248 private storage and operator-secret settings remain server-managed.

The endpoint:
1. Reads the private history via **SQLite mode=ro/query_only** and validates the **entire Step247/248 HMACed record and timeline chain**, all source/claim bindings, and the last historical observation. Reject invalid history **before** network egress.
2. Calls **`answer_original_source_claim` directly in-process exactly once**, reusing the existing official-source HTTPS reader, strict claim/quote assurance, freshness gate and bounded policy. This is *not* a nested internal HTTP call.
3. Converts the rendered answer using the already trusted `interpret_cited_answer` contract, then applies the same Step246 deterministic comparison via the refactored **pure** `reconcile_observations` function. Existing Step246 callable retains its behavior and prefetch validation.
4. Reopens and independently verifies the whole timeline again; refuses any changed most-recent record, invalid entry or concurrent append. No write lock spans HTTPS; there is **no implicit history append**.
5. Returns only **bounded decisions**, previous/current capture SHA-256, quote SHA-256, observed UTC times, request-binding digest, root and latest baseline IDs, and conservative status. **No publisher quotes, tokens, paths or raw HTML** are returned. Source unavailable/ambiguous, invalid current freshness, invalid baseline, or race => `abstain` with **no partial evidence**.

The defensive app client `check_temporal_reconciliation_with_api(client,token,claim,root)` sends one authenticated HTTP request, requires a reliable caller-owned TLS transport when remote, and verifies strict flags, root/request ID, monotonic UTC timestamps, fresh current observation, SHA coherence and change classification. It returns no partial observations on errors.

## Guarantees and limits

- Historical baselines can be old solely for **comparison**; they never become current evidence. Only the newly and separately fetched source statement can be eligible for *bounded current-source support*, and support is not objective truth.
- No unsupported promotion from LLMs/neural outputs or dual-host assumptions. Source truth, publisher identity, historical clock authority, source ownership, completeness of an operator-held timeline and operator rollback **remain unverified**.
- This is one explicitly requested source fetch per authorized operation, not background monitoring, autonomous polling, a tracking system or deployment. The API is still the restricted local single-tenant pilot; external HTTPS release [issue #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242) remains OPEN/deferred.
- The history database is never modified by reconciliation, including failure paths. Previously implemented CLI append remains separately opt-in.

## Reproducible local operator workflow

With Step249 pilot settings plus `ARL_TEMPORAL_RECHECK_API_ENABLED=1` securely configured **on the server**, use a previously saved `root_record_id` with the same exact `OriginalSourceClaimRequest`:

```python
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.temporal_recheck_client import check_temporal_reconciliation_with_api

request = OriginalSourceClaimRequest(
    claim_text="Python 3.13.0 is a stable release.",
    entity="Python 3.13.0",
    source_uri="https://www.python.org/downloads/release/python-3130/",
    freshness_max_age_seconds=3600.0,
)
# client is a caller-managed TLS/authenticated HTTP transport or a trusted
# local TestClient; token is an operator secret, never placed in code or logs.
report = check_temporal_reconciliation_with_api(client, token, request, root_record_id)
if report.outcome == "bounded_reconciliation":
    assert report.may_use_historical_as_current_evidence is False
```

## Strict completion requirements

- [ ] Real authenticated API + deterministic comparison + defensive application client merged without regressions.
- [ ] Adversarial tests: valid single-source unchanged capture, changed text/quote, contradiction, offlist, missing bearer/opt-in, wrong canonical claim, tampered record/link/key, publisher outage/ambiguity, missing history, corrupt source response, race on latest timeline, malformed client schema, fake truth flags, timestamps, SHA mismatches and transport errors.
- [ ] Reused existing source-history CI workflow: run all focused tests and three genuine authenticated CLI publisher source captures followed by **exactly one** additional genuine HTTPS observation through reconciliation endpoint + defensive app client. Show no DB modifications and never claim publisher changed.
- [ ] Full backend regression and all 21 GitHub Actions PR checks success, merge PR, then independently recheck **all 21 push workflows on the exact final main SHA** and inspect focused, full and real-source logs.
- [ ] Record verified final acceptance on merged PR *without* a post-verification source commit; preserve external deployment issue #242.
