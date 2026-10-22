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
