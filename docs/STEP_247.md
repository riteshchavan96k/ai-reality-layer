# Step 247 — Operator-controlled durable original-source observation history (scope before implementation)

## Verified checkpoint and missing product workflow

Independently read actual `main` at `db67b59258781be277aab7819e05c47465bb8c12`: accepted Step246 (feature PR #274, audit PR #275), **20/20 exact-main successful push workflows**, full backend **2,971 passed**, focused Step246 **35 passed**, and two real Python.org HTTPS fetches via authenticated local CLI. No earlier Step247 specification exists.

`backend/app/integrations/source_recheck.py` rechecks a caller-held `ClientCitedAnswer`, and `backend/app/cli.py --recheck` captures twice *within a single invocation*. A developer cannot yet store a validated observation and use it in a later independent CLI process. Existing `PersistentOutcomeMemory` is SQLite storage for execution outcomes, not original-source evidence.

## Required actual product functionality

- Opt-in, local-only `--save-observation` records one *fully validated* original-source claim observation; `--recheck-record <id>` opens that record in a later process and performs **exactly one** fresh verified authenticated API source fetch. Both use the unchanged `--live`, pilot token, HTTPS URL allowlist, claim/entity identity and request freshness gate. Existing `--recheck` remains intact.
- Source history is dedicated to this workflow, not mixed with execution outcome memory. Use bounded SQLite records, a fixed schema, private operator-owned store directory and file, strict size/record ceilings, and atomic database transactions. No raw quotes, tokens, secret keys or source bodies in normal output; required saved original-source statement is treated as untrusted data.
- Every saved baseline is protected by a keyed HMAC over canonical record bytes bound to its random identifier. Key is a high-entropy environment secret and is never stored in the database or logged. Verify MAC before interpreting any record or making any outbound request. Reapply Step246 exact request/quote/time/decision grammar validation before egress. Missing key, corruption, mismatch, altered/absent history => conservative abstention/refusal with no partial citations.
- Old stored captures are history only; only new independently observed evidence can be eligible as *current bounded evidence*. An HMAC is NOT third-party attestation, trusted chronology, publisher authorship or protection against same-operator rewrites/rollback. No general truth, automatic monitoring, external deployment or broad semantic inference.
- Adversarial authenticated FastAPI tests use mocked source bodies for changed/unchanged/contradiction, corrupted rows, wrong keys, missing/off-list source, preflight auth, recheck source failure and cross-process persistence. Add a *real* Python.org HTTPS two-process opt-in smoke workflow, in addition to **all previous 20 workflows**. No fabricated real-source historical changes.
- Preserve Step234 externally hosted release gate (#242 OPEN/deferred). Do not mark Step247 complete until code and tests pass in PR, the PR merges, **all 21 push workflows on exact final main SHA succeed**, full regression passes, focused tests and real HTTPS canary pass, and final acceptance is recorded without an additional unverified merge.

## Operator limits and acceptance

This is a concrete durable source observation workflow for AI Reality Layer, not a general-purpose surveillance store. Single source per operation; explicit physical/operator authorization and approved exact source URL remain required. Do not introduce scheduler, external hosting, arbitrary source discovery, or promote neural NLI to authority.
