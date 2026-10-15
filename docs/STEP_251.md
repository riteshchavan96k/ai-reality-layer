# Step 251 — Privileged authenticated Reality State timeline creation and atomic append

## Independently verified starting point

Step250 merged [PR #279](https://github.com/riteshchavan96k/ai-reality-layer/pull/279) at exact `main` `4ff63821fcc53637006f5e50acc68a05eeae2ff8` and was accepted with 21/21 successful exact-main GitHub Actions, 3,106 passing full backend tests, and genuine Python.org live/history API verification. We verified `docs/STEP_251.md` was absent. This milestone addresses a verified product gap: existing authenticated apps could read or recheck persisted evidence but could not **create or append** that history without manual CLI commands.

## Genuine functionality

Two explicit authenticated application endpoints:

- `POST /api/v1/reality-state/timeline/create` — one fresh server-observed original-source claim, saved as a MAC-verified initial record with a random durable root ID.
- `POST /api/v1/reality-state/timeline/append` — requires the existing root, exact claim, and **expected latest record ID**; verifies complete history before any source read, captures one new original-source observation, revalidates latest under SQLite `BEGIN IMMEDIATE`, then commits new receipt + edge + retry ID in one transaction.

The input to `create` is `{ "operation_id": "<32 lowercase hex>", "claim": { "claim_text": "...", "entity": "...", "source_uri": "https://...", "freshness_max_age_seconds": 3600.0 } }`. Append also includes `root_record_id` and `expected_latest_record_id`. Every operation ID must be unique to that intended logical write and stable across client retries. For different writes, **generate a new unpredictable 128-bit operation ID** (e.g. `secrets.token_hex(16)`). History record IDs are generated server-side.

Both require:
- Existing `ARL_RUNTIME_MODE=pilot`, server-managed high-entropy `ARL_PILOT_BEARER_TOKEN` and `Authorization: Bearer …`;
- Exact operator-allowlisted original-source HTTPS URL (`ARL_INDEPENDENT_SOURCE_ALLOWED_URLS`);
- Explicit opt-in **`ARL_TIMELINE_WRITE_API_ENABLED=1`** and a distinct high-entropy **`ARL_TIMELINE_WRITE_TOKEN`** whose value must **differ** from the pilot bearer;
- Client request header `X-ARL-Timeline-Write-Token` holding that separate writer secret. Normal pilot bearer **alone never grants write authority**;
- Private operator-owned directory and SQLite store, `ARL_OBSERVATION_STORE_PATH` and `ARL_OBSERVATION_HMAC_KEY_HEX`, configured securely on server. Only HTTPS or trusted local TestClient transports should ever carry these bearer credentials.

Existing Step249 read-only timeline and Step250 non-mutating reconciliation APIs keep their original behavior and do **not** require the writer header. They cannot create or append history.

## Durability, retry and conflicts

The server still uses Step247 validated source records, Step248 MACed ordered links and Step246 bounded change classification. The additional local `timeline_write_operations` ledger is MAC-keyed with independent domain separation and stores each random operation ID, exact canonical claim binding, write kind, root, expected head, new record ID, sequence and status. Each successful record, edge and keyed retry receipt is persisted in **one SQLite transaction**. There is no partially successful history on rollback.

- A **completed** operation replay with the same ID **and the exact same request** is validated against the complete saved timeline and returns the original record ID with `replayed=true`, **without another publisher request**. Replays still work if subsequent authorized appends advanced the timeline.
- Reusing an operation ID with a different claim, root, expected head or write kind **abstains before source egress**. Corrupted operation metadata/MAC abstains.
- An in-flight concurrent duplicate can perform another source fetch, but the serialized SQLite write gate ensures **only one durable record**. Retry protection is *exactly-once persistence per validated logical ID*, not global exactly-once HTTP egress.
- Another write that advances the expected head before append commit causes a fail-closed refusal; the client must explicitly retrieve the new historical head and decide whether to retry as a **new** intended operation. No silent overwrite, history truncation or hidden retry.
- Per-timeline cap remains 64 and global source observation cap remains 1,000; the operation ledger is also capped at 1,000 entries. No auto-pruning, background polling or scheduled writes.

Every successful API receipt contains only record identifiers, bounded status/decision, source quote/capture SHA-256, UTC observation time and explicit non-authority flags. **No original-source quote, raw HTML, operator HMAC, bearer or database path** appears in successful or failure receipts. Failed source verification, unapproved URLs, unavailable private storage, tampering, invalid claim or full capacity never create an affirmative receipt.

Application client `write_timeline_with_api(client, bearer, writer, claim, operation_id, root=..., expected=...)` checks response identity, strict authority flags, record/sequence consistency, clock chronology, response size/content type and redacted non-current historic evidence semantics; it never retries automatically.

## Verification acceptance

- [ ] Separate writer bearer and opt-in enforced **before network egress and disk writes**; normal bearer cannot modify.
- [ ] API-only creation and repeated appends work with Step249 history inspection and Step250 live reconciliation.
- [ ] Saved identical operation retry does not duplicate history or network; reusing IDs for another claim/kind/head fails before egress.
- [ ] Tampered HMAC/links/receipt, corrupted store, stale head, publisher errors, truncated/invalid request, arbitrary URL or storage exhaustion cannot yield positive partially committed evidence.
- [ ] Adversarial race and injected transaction failure checks demonstrate atomicity and no duplicate persistent receipts.
- [ ] Genuine Python.org HTTPS canary uses **only the authenticated API** for two source-backed writes (create + append), then confirms Step249 read and Step250 source recheck. Verify the separate credentials, retries, and no unrequested monitoring, without inventing publisher content change.
- [ ] All 21 PR checks succeed, full backend suite and existing source/neural/container regressions; merge the PR then **independently check all 21 exact-final-main push workflow results**, focused and real HTTPS job logs, and full backend logs before recording acceptance on the merged PR (not by another unverified commit).

## Limits and deferred release gates

This is a locally secured **single-tenant** operator pilot; all holders of writer secret share writer authority. Additional multi-tenant scoping, hosted ingress TLS, rate limits, quotas, resource/cost isolation, secret lifecycle and operator audit policy are NOT established by this step. HMAC is operator-held integrity, not an independent publisher signature, tamper-proof anti-rollback historical attestation, trusted timestamp or proof of actual real-world truth. Publisher source statement changes are not certified as reality changes. Genuine app functionality, not general LLM autonomy.

External authenticated HTTPS pilot deployment remains separately open and mandatory at [issue #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242). Never claim deployment completed based on CI's local TestClient or actual outbound source TLS alone.
