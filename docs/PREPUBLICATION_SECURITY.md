# AI Reality Layer — publication security review

## Current status (22 October 2026)

The owner intentionally changed this repository to public. The proprietary
LICENSE is already on main at 075780ace3f7e3888b21bf0ba1e6bde1de9369d8.
This review does not change visibility, grant reuse rights, certify ownership,
or declare the repository free of secrets. Step 255 PR #284 remains separate.

The earlier statement that full Git history could not be scanned is superseded
by the local review described below. Account billing was a suspected CI cause;
it was not independently proven. All 24 project workflows on the above main
commit now pass on attempt 2, including 3,276 backend tests. The separately
managed dependency-graph run 39761938781 cannot be retried through the API
(403: workflow run cannot be retried); it is not counted among those 24.

## Engineering changes in PR #286

- Ignore local credential files, environment variants, keys and databases.
  Ignore private audit output paths too. Ignore rules never erase history.
- Read-only scanner screens reachable blob, commit and tag objects without
  printing matched values. It decodes BOM-marked UTF-16 before screening,
  checks every committed tree for sensitive aliases, flags LFS/submodule
  exclusions and refuses shallow clones or replacement refs.
- Five synthetic regression tests cover deleted credentials, no false
  publication clearance, UTF-16 and commit-message findings, identical-blob
  sensitive aliases, and refusal of shallow history.
- Full local backend regression: 3,281 passed (Python 3.12).

## Reproduction

Use a trusted complete clone and fetch all advertised branches, tags and PR
heads/merge refs. Never use an untrusted existing clone with replacement refs.
For example, create a fresh mirror, then explicitly fetch PR refs:

```bash
git clone --mirror https://github.com/riteshchavan96k/ai-reality-layer.git ai-reality-layer-audit.git
git -C ai-reality-layer-audit.git fetch origin '+refs/pull/*/head:refs/pull/*/head' '+refs/pull/*/merge:refs/pull/*/merge'
python scripts/prepublication_history_audit.py ai-reality-layer-audit.git > private-audit.json
python -m pytest -q backend/tests/test_prepublication_history_audit.py
```

Exit 1 means findings need triage; exit 2 means inspection did not complete.
Exit 0 is never publication clearance. Do not upload raw finding reports to a
public PR. Independently scan historical content with a maintained separate
detector, not just this project's patterns. The review uses detect-secrets
1.5.0 outside backend dependencies; heuristic detection is not provider-side
credential verification and zero matches cannot prove absence of secrets.

## Required remaining review boundaries

Account secret stores, collaborator roles, organization policies, inaccessible
or expired logs/artifacts, caches, attachments, unadvertised/unreachable Git
objects, third-party rights and confidential business material require their
own review. A secret scanner and commit author names cannot settle those.
Record actual coverage and exclusions; never replace missing evidence with a
clean result. No compromised credential has been established by the completed
targeted triage, and no credential rotation or history rewrite has occurred.

If a real secret is confirmed, revoke/rotate at its provider first, investigate
use, then coordinate any precise history cleanup with the owner. Do not force
push or delete branches speculatively. Existing clones, forks and cached PR
objects require separate treatment even after a rewrite.

The original PR's comprehensive publication-clearance gate remains unmet until
all required surfaces and owner-only controls have been reviewed. Keep that
claim separate from successful engineering tests and restored CI. Do not mark
Step 255 complete or merge it based on this security work. External deployment
issue #242 remains open.

## Completed audit evidence — 22 October 2026

Reviewed main: `075780ace3f7e3888b21bf0ba1e6bde1de9369d8`.
Reviewed security implementation: `19a629083924f040216fc1d5063d14a30ce2e3fc`.

- Advertised remote inventory: 399 branch heads and 263 PR head/merge refs.
  Every advertised object was present in the full local checkout; no advertised
  tags were returned. Local refs also include tracking refs and a local merge.
- Initial history snapshot: 1,973 unique blobs and 2,376 commit/tag objects.
  The independent detect-secrets 1.5.0 file-aware scan covered all 4,349
  objects, decoding UTF-16 where necessary. Its 15 unique findings were
  contextually reviewed: synthetic rejection/redaction-test credentials,
  public model/dataset hashes and revisions, recorded commit IDs, and a
  workflow block generating and masking a fresh ephemeral token. No live
  provider credential was established by this triage.
- After fetching the updated security commit, the enhanced project scanner
  screened 1,977 blobs, 2,377 commit/tag objects and 1,978 distinct committed
  trees across 665 local refs. Its six credential-URL findings were historical
  test-fixture versions using example domains; two license blobs were the
  deliberate proprietary notices. The former binary finding was UTF-16
  requirements text, now decoded and screened. No sensitive-path, LFS,
  submodule, undecodable-text or oversized-object finding was reported.
- Actual current-main backend log: [run 39754071167, attempt 2](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/39754071167):
  **3,276 passed in 13.80s**. All 24 project push workflows succeeded.
- Security PR implementation backend log:
  [run 39767948123](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/39767948123):
  **3,281 passed in 14.96s**. All 24 PR workflows succeeded on the exact
  implementation SHA above. Later documentation commits require their own CI.
- Targeted live-key-pattern screening completed on 48 job logs: the 24
  current-main reruns and the 24 accepted Step254 main runs. No matches to
  the screened GitHub/OpenAI/private-key/AWS/Hugging Face patterns were found.
  This is pattern screening, not a guarantee of absence of arbitrary secrets.
- Downloaded and inspected all ten retained audit JSON artifacts produced by
  Steps222/226/227/232/233 on those two checkpoints. They contained audit
  metrics, public-source excerpts/receipts and hashes; no matches to the
  project's credential patterns were found. No GitHub releases were listed.
- API inspection returned no repository rulesets; main reported unprotected.
  Account metadata alone does not establish safe collaborator or secret-store
  configuration. Those administrative surfaces were not inspected.

## Explicitly unfinished comprehensive gate

The run inventory contained 2,234 historical workflows. A broader log sweep
was interrupted before its final results were saved; only the 48 completed
checks above are credited. Older logs, prior attempts, artifacts and caches,
PR/issue discussions and attachments, unavailable/deleted objects, account
secret stores and collaborator settings are **not fully cleared**. Neither
scan verifies the contractual ownership chain or provider-side token validity.

PR #286 must remain unmerged under its original comprehensive gate until
remaining review evidence is supplied. Successful CI and synthetic-fixture
triage do not silently waive that gate. No keys were rotated, no history was
rewritten, no branches were deleted, and no visibility change was made here.
