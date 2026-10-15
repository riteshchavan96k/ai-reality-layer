# Step 248 — Verified longitudinal Reality State tracking and evidence-change timeline

## Predecessor independently verified before work

Step247 accepted via merged [PR #276](https://github.com/riteshchavan96k/ai-reality-layer/pull/276), exact main `5bd54d4f481e28662a5d122d61fb268749373097`. Checked 21/21 completed successful push workflows, 3,001 full backend passing tests, 30 dedicated Step247 tests and real two-process HTTPS source history. No prior `docs/STEP_248.md` existed. Step234 externally deployed HTTPS pilot remains a separate open release gate ([issue #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242)).

## Actual product limitation addressed

Step247 `--recheck-record` compared a caller-held baseline with one new verified HTTPS reading, but discarded the new observation rather than storing it in an evolving history. The existing history could not select the latest validated observation or provide a bounded change timeline. Step248 adds **operator-triggered successive observations** for one exact claimed statement and one approved publisher URL, using the unchanged independently observed backend evidence policies and Step246 recheck algorithm. It is not a generic search, real-world truth monitor or authorized autonomous action system.

## Commands and prerequisites

Preserve Step247 operator environment setup: explicitly approved pilot runtime, bearer secret in environment, fixed original-source HTTPS URL allowlist, dedicated private directory and database (`ARL_OBSERVATION_STORE_PATH`) and **persistently managed** 32-byte operator HMAC key (`ARL_OBSERVATION_HMAC_KEY_HEX`). Never put keys in GitHub history, command arguments or output. Claim, entity, source URL and exact freshness window must match throughout.

```sh
# First operator-authorized original-source fetch and saved baseline.
python -m backend.app.cli --live --save-observation --claim "Python 3.13.0 is a stable release." --entity "Python 3.13.0" --source "https://www.python.org/downloads/release/python-3130/"
# Copy only its random saved_record_id, used as ROOT_ID in following commands.

# Later operator-authorized real HTTPS fetch: compare latest and append atomically.
python -m backend.app.cli --live --timeline-append ROOT_ID --claim "Python 3.13.0 is a stable release." --entity "Python 3.13.0" --source "https://www.python.org/downloads/release/python-3130/"

# Later (even after restarting): retrieve verified change history without HTTPS.
python -m backend.app.cli --timeline-show ROOT_ID --claim "Python 3.13.0 is a stable release." --entity "Python 3.13.0" --source "https://www.python.org/downloads/release/python-3130/"
```

`--timeline-show` requires existing authenticated pilot settings, fixed source allowlist and operator-keyed private history but **does not** require `--live` and **must never fetch a source**. `--timeline-append` requires explicit `--live` and performs *at most one* approved HTTPS source fetch. The fresh validated observation is stored together with its keyed link in **one SQLite transaction**. Old Step247 baseline record IDs can be adopted as a timeline root. The prior Step247 `--recheck-record` behavior remains backwards compatible.

Each timeline entry is keyed by a random record ID; an independently MAC-protected edge describes the root, sequence, previous record, and bounded Step246 change classification. Timeline inspection revalidates **every** edge, saved record, exact request and adjacent classification before returning output. The latest verified entry is preflight checked **before network egress**; the entire chain is verified again within a serialized write transaction, refusing stale/concurrent writers. No partial history or partly appended receipt is returned after an error. Maximum timeline length is 64 observations; global Step247 local store ceiling remains 1,000 observations; no automatic pruning or retention policy is introduced.

## Honest safety and epistemic limits

- HMAC is operator-controlled record integrity, **not** independent publisher-signed provenance, a trusted clock, third-party timestamp, external authorization or tamper-proof/anti-rollback evidence. Deleting the end of a valid chain or replacing the entire operator-controlled database is outside this threat model.
- Classification is about exact source capture hash, bounded quotation and source-claim relationship. A publisher may change unquoted HTML without its bounded statement changing; a changed statement is **not proof of a real-world factual change**.
- Previously captured evidence is historical only; never eligible as fresh evidence. Each new append requires fresh independent server-side original-source HTTPS observation through the existing authenticated pilot API and the existing conservative grammar policy. Source failures/ambiguous quotes cause abstention without a new timeline entry.
- Timeline output contains timestamps, SHA-256 hashes, decisions, classifications and random record IDs, **not raw untrusted publisher quotes by default**. The local SQLite database contains those untrusted quotes; operator is responsible for backup, disk-level protection and secure deletion.
- No background monitoring, network-exposed deployment, domain ownership proof, general NLI authority, publisher-authenticated chronology or broad claim understanding is included.

## Final Step248 completion gate (do not mark before checked)

- [ ] Implementation merged after all PR-head CI checks succeed.
- [ ] Focused mock-publisher adversarial tests cover three observations, changed bounded statement and quote, off-list/missing opt-in, claim mismatch, corrupt link/record, wrong HMAC, concurrent stale writer, atomic rollback, limit preflight and never leaking partial receipts.
- [ ] One existing CI workflow additionally runs **genuine Python.org HTTPS** in three separate authenticated command processes, then opens history in a fourth offline inspection process, without inventing a real publisher change.
- [ ] Entire Python backend regression passes; all 21 applicable GitHub Actions `push` runs pass on the **exact final merged `main` SHA**; inspect focused and full job logs.
- [ ] Record immutable acceptance audit on merged PR without another unverified commit, maintain Step234 deployment blocker as OPEN/deferred.
