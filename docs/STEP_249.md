# Step 249 — Authenticated read-only temporal Reality State API and defensive developer client

## Verified predecessor and precise scope

Step248 was accepted at exact merged `main` `729fb1b43972faed68c3b541822d3a731a2e55b4` ([PR #277](https://github.com/riteshchavan96k/ai-reality-layer/pull/277)), with 21/21 successful exact-SHA push workflows and 3,022 backend passing tests. Genuine HTTPS canaries verified three independently captured official-source observations across distinct CLI processes. No preexisting Step249 specification was found.

Step248 provides an operator-only local CLI to append and inspect a narrowly source-bound timeline. **Real AI applications cannot yet consume that timeline through an authenticated network/API contract**. The new Step249 goal is limited to that gap. No new automated HTTPS reads, active monitoring, publisher signatures, independent historical attestation, or external deployment is authorized.

## Product functionality

- A new `POST /api/v1/reality-state/timeline` returns **previously recorded historical observation metadata only**. Input: `{ "root_record_id": "<32 lower-case hex>", "claim": { "claim_text": "...", "entity": "...", "source_uri": "https://...", "freshness_max_age_seconds": 3600.0 } }`. The claim request must match the saved canonical request including the numeric freshness representation.
- Pilot access uses the **existing bearer-authorization middleware**, plus a separate explicit `ARL_TEMPORAL_HISTORY_API_ENABLED=1` operator opt-in. If pilot is not enabled, or the source is not in the operator's exact HTTPS allowlist, the read abstains before inspecting evidence. Incorrect authorization gets 401 from existing middleware. The operator-only local storage and HMAC secret remain **server-side environment settings** and are never sent by the developer app.
- Server uses a dedicated **read-only** history settings accessor and `sqlite3` `mode=ro`, `PRAGMA query_only=ON`. The history reader checks private owner/file permissions and reuses Steps247–248 MAC validation for the complete timeline, each record, every edge, claim binding and adjacent source change classification. Unlinked (one-entry) history is supported without attempting to create its timeline table. The endpoint must neither open nor create history DB files in write mode, and must never call the independent-source reader or fetch a publisher.
- Structured schema returns at most 64 observations, with random record IDs, historical source UTC observation times, decision labels, source capture/quote hashes and verified bounded *change classifications*. It never returns raw source HTML, publisher quotes, database paths, bearer tokens, HMACs or key material. A failed operation returns `outcome="abstain"` and a null timeline; no partial evidence.
- The defensive app client `check_temporal_timeline_with_api(client,token,request,root)` makes one authenticated request. `interpret_temporal_timeline(...)` checks exact root/request binding, strict JSON types/boolean-ceiling flags, count/sequence, unique record IDs, chronology, hashes, decision statuses, adjacent change classification and response size/content-type. Invalid/altered/unauthorized responses fail closed without partial receipts. **A correctly returned old source observation remains historical, never current evidence.**

## Operator use

Keep Step247/248 private owner-only local database and operator-managed 32-byte keyed HMAC settings. Configure `ARL_RUNTIME_MODE=pilot`, `ARL_PILOT_BEARER_TOKEN`, `ARL_INDEPENDENT_SOURCE_ALLOWED_URLS`, `ARL_OBSERVATION_STORE_PATH`, `ARL_OBSERVATION_HMAC_KEY_HEX`, plus `ARL_TEMPORAL_HISTORY_API_ENABLED=1` **in the server environment only**.

The developer supplies its authorized pilot token and an exact root/claim via an authenticated TLS-protected client (or local controlled TestClient):

```python
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.temporal_timeline_client import check_temporal_timeline_with_api

request = OriginalSourceClaimRequest(
    claim_text="Python 3.13.0 is a stable release.",
    entity="Python 3.13.0",
    source_uri="https://www.python.org/downloads/release/python-3130/",
    freshness_max_age_seconds=3600.0,
)
# client: caller-owned authenticated TLS HTTP client or an authorized local
# TestClient; token: operator-provisioned secret never logged or hardcoded.
history = check_temporal_timeline_with_api(client, token, request, root_record_id)
if history.outcome == "verified_historical_timeline":
    # Historical, bounded source-evidence metadata ONLY.
    assert history.may_use_as_current_evidence is False
```

The existing CLI save, recheck, append and inspect behavior is preserved; **no automatic public Internet hosting is established**.

## Limits and safety

- Caller-owned transport must be authenticated and TLS-secure when remote. Pilot bearer control is a **single-tenant** boundary; all authorized holders share the configured operator history. No multi-user tenancy, scoped access control, arbitrary file paths or history write endpoint is provided.
- HMAC validates operator-held records, not independent publisher authorship, time authority, anti-rollback history, real-world factual truth or independent source ownership.
- Only original explicitly allowlisted source history is returned, with no publisher HTTPS reads. Existence of historical evidence is **not** a license to answer a current-time question without fresh source verification.
- The strict client validates structural/semantic consistency of declared history, not cryptographic publisher origin or an independently signed guarantee that the server returned *all* possible historical records. Caller must trust its authenticated API transport and history operator.
- Step234 external HTTPS pilot release issue #242 stays OPEN/deferred. Do not claim general production readiness.

## Acceptance gate

- [ ] Implement endpoint, strict Pydantic contract and defensive app client.
- [ ] Adversarial API tests for genuine authenticated local three-entry history, missing bearer, offlist and mismatched claims, no opt-in or development fallback, missing DB or corrupt MAC, no raw publisher data, **zero new source reads and zero SQLite writes**, and faithful read-only unlinked-baseline handling.
- [ ] Adversarial consumer tests for forged truth flags, invalid JSON types, timelines with missing/duplicated records, inconsistent decisions, non-monotonic times, changed hashes and incorrect statuses, invalid claim binding, and invalid transport or bearer.
- [ ] Genuine publisher HTTPS CI: save and append three Python.org readings through separate authorized CLI processes, then consume the *existing* persisted history via FastAPI plus strict client. Refuse any attempt to fetch source from the read-only endpoint. Do not manufacture a real publisher change.
- [ ] Full backend regression, all existing genuine-source/neural/pilot workflows successful on PR head, merge PR; then independently check **all 21 successful push workflows on the exact final merged main SHA**, focused/real-source logs and full regression.
- [ ] Record final acceptance audit comment on the merged PR without another code commit, preserving verified final main SHA.
