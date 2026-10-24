# AI Reality Layer — publication security review

## Reconciled post-Step255 security checkpoint — 24 October 2026

**PR #286 remains DRAFT, NOT MERGED, and is NOT a declaration of complete
historical publication clearance.** The repository is already public.
This review records all retrievable evidence and known blind spots without
pretending that deleted materials or external account secrets were examined.

After the original 22–24 October security review, the following independent
changes landed on protected `main`:

- [PR #287](https://github.com/riteshchavan96k/ai-reality-layer/pull/287):
  all preexisting GitHub Actions references pinned to immutable action commits,
  then tested with 24/24 exact-main push workflows.
- [PR #288](https://github.com/riteshchavan96k/ai-reality-layer/pull/288):
  production `backend/requirements.txt` converted to strict UTF-8 with
  **14/14 pinned dependencies preserved**. The separately managed
  [dependency-graph run 40101625658](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/40101625658)
  succeeded and submitted the `pypi::/backend` manifest.
- [PR #284](https://github.com/riteshchavan96k/ai-reality-layer/pull/284):
  original Step255 question API merged; authentic final-main official-source
  benchmark 10/10 narrow cases and 25/25 workflows passed. This is **product
  engineering**, not evidence that historic repository secrets are cleared.
- [PR #289](https://github.com/riteshchavan96k/ai-reality-layer/pull/289):
  the *non-destructive* `.gitignore` credentials/datasets protection and
  read-only historical scanner/tests were independently extracted from this
  audit PR and merged alongside milestone documentation updates. Exact final
  protected main: `d349e6882989b523727fb794295d2e29d4570e64`, **25/25 push workflows passing**, with
  [full backend run 40106187879](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/40106187879)
  showing **3,354 passed**, including six scanner/ignore regressions.
  [Step255 real-source run 40106187840](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/40106187840)
  independently passed the bounded source/model evaluation.

**Scope reconciliation:** this PR has now been based on the latest merged
main, preserving its old history via a non-force merge. All scanner/test,
ignore, UTF-8 and product changes described below are already integrated.
The expected *effective* PR diff is **only this audit documentation file**.
The chronological audit sections below describe when each observation was
made; older "pending" statements are historical, not current engineering
failure assertions. In particular, dependency-graph parser recovery and
action-tag pinning (previous risk register items R4 and part of R5) have
been technically resolved.

**Still open or bounded:** R1 historical cache *bytes*, R2 inaccessible or
deleted/off-platform artifacts, R3 external provider credential inventory,
R5 **required CI-status-check enforcement (owner-admin configuration)**,
R6 independent IP/license-chain review, and R7 separately deferred external
HTTPS deployment. Successful CI, current alerts showing zero and a
non-clearance scanner cannot prove those surfaces are clean. The owner's
prior declaration about no unauthorized third-party/employer/client content
remains a self-declaration, not a contractual legal audit.

**Security decision: HOLD this audit PR as draft.** No blanket risk
acceptance, credential rotation, cache deletion, history rewrite, deployment
or branch-ruleset administration was performed through this reconciliation.
The independent legal/security residual-risk acceptance decision belongs
to the owner. The next product milestone (Step256) is **not** defined here.


## Historical engineering status (22–24 October; current update above supersedes)

The owner intentionally changed this repository to public. The proprietary
LICENSE is already on main at 075780ace3f7e3888b21bf0ba1e6bde1de9369d8.
This review does not change visibility, grant reuse rights, certify ownership,
or declare the repository free of secrets. Step 255 PR #284 was still separate at the time; its later acceptance is documented in the current checkpoint above.

The earlier statement that full Git history could not be scanned is superseded
by the local review described below. Account billing was a suspected CI cause;
it was not independently proven. All 24 project workflows on the above main
commit now pass on attempt 2, including 3,276 backend tests. The separately
managed dependency-graph run 39761938781 cannot be retried through the API
(403: workflow run cannot be retried); it is not counted among those 24.
Its job log reports a file-fetcher error: invalid byte sequence in UTF-8.
The backend requirements manifest was UTF-16; this PR converts it to UTF-8
while preserving all 14 dependency specifications. Local strict UTF-8 parsing
and dependency-line equivalence checks pass. The managed graph job on main
is still failed; recovery must be verified by a fresh successful run after
the correction reaches main.

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
- Convert backend/requirements.txt from UTF-16 to UTF-8 so Dependabot can
  read the manifest. No dependency versions change.

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

## Completed audit evidence — 22–23 October 2026

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
- The historical run inventory contained 2,282 runs. Every inventory ID was
  reconciled against durable review records: 2,142 latest-attempt job logs
  were screened, including two successful retrieval retries; 104 jobs had no
  executed steps and 36 runs returned no jobs. No matches to the targeted
  GitHub/OpenAI/private-key/AWS/Hugging Face/Slack patterns were found.
  All 25 prior attempts were inspected separately: each had zero steps and
  no assigned runner. Empty/unavailable job records are not screened logs.
  Pattern screening cannot prove absence of arbitrary secrets.
- Inventoried artifacts across all 2,282 runs: 691 retained archives, each
  containing one readable JSON file. All 691 were downloaded and screened
  with the same targeted patterns, with no matches, decode failures or
  download failures. No expired artifacts were returned in this inventory;
  already deleted artifacts are outside this evidence.
- Screened all 286 issue/PR descriptions and 59 issue comments with the same
  targeted patterns: no matches. No PR review comments were returned and no
  GitHub attachment links were detected in those bodies. GitHub Discussions
  are disabled; no releases were listed. External linked content and deleted
  discussions/attachments are outside this coverage.
- Reviewed current workflow configuration: all 24 workflows declare
  `contents: read`; none contains a repository-secret expression or a
  `pull_request_target`/`workflow_run` trigger. Sixteen use setup-python's
  pip cache. This reviews configuration, not historical cache contents.
- API inspection returned no repository rulesets; main reported unprotected.
  Account metadata alone does not establish safe collaborator or secret-store
  configuration. Those administrative surfaces were not inspected.

## Owner-reviewed repository settings — 24 October 2026

The repository owner inspected authenticated GitHub settings and security pages
and supplied screenshots within the project conversation on 24 October 2026.
These observations are owner-provided UI evidence, **not** a public export of
private account settings, a forensic scan, a contractual IP audit, or a proof
that no unknown credential or exposure exists. Do not place screenshots,
credential values or private cache contents into this public repository.

### Access, automation and protections

- Repository remains **public** and owned by `riteshchavan96k`; the connected
  GitHub repository API reports the owner has `admin` permission.
- The Collaborators page displayed **zero additional direct collaborators**.
  No deploy keys, repository webhooks, self-hosted Actions runners or GitHub
  deployment environments were listed. These pages alone do not prove the
  absence of access from other account-level services or previously issued tokens.
- The Actions configuration pages displayed **no repository/environment
  secrets or variables**. Other secret stores, personal tokens, external
  hosting configuration, historical deleted settings and credential providers
  were not independently audited. No secret value was requested or disclosed.
- The Installed GitHub Apps page showed **ChatGPT Codex Connector** as the only
  listed app; the owner explicitly chose to retain it. Installation privileges
  and any access outside this repo need separate review if scope expands.
- GitHub Ruleset **25773872**, "Protect AI Reality Layer Main", was verified
  directly through the repository API as `active`, targeting
  `~DEFAULT_BRANCH` (currently `main`), with branch deletion restricted,
  non-fast-forward / force updates blocked, and pull requests required.
  The bypass list is empty. Required approving review count is **zero**;
  **required status checks are not enforced by the ruleset**. This protects the
  branch against specified direct modifications, **not** against intentionally
  merging an untested or malicious PR. The connected branch API reports
  `protected=true`. The prior 22–23 October "unprotected" observation
  in the historical audit below was accurate *then*, and is superseded.
- GitHub Actions owner screenshots show default workflow-token access scoped
  to read repository contents/packages, and workflow-created/approved PRs
  disabled. The policy still allows all reusable/third-party actions; requiring
  full commit-SHA pinning is **off**. Existing workflow versions must first be
  migrated and verified before tightening that control. Owner reported
  changing external-fork contributor approval, and GitHub displayed
  "settings saved"; the final selected radio option was not independently
  reconfirmed. Retention setting displayed **90 days**.
- The owner showed Dependency graph and Dependabot alerts **enabled**;
  Dependabot security-update and grouped-update automation remained off.
  The open/closed Dependabot vulnerability-alert screen showed **0 / 0**.
  The previously failed managed dependency-graph run remains unresolved on
  `main` until the UTF-8 requirements repair in this PR is merged and a
  **fresh successful graph execution** is observed. Consequently, zero
  Dependabot alerts is not equivalent to complete vulnerability coverage.
- Owner displayed GitHub **Secret Protection enabled**, reported enabling
  **push protection**, and the Secret scanning alert screen showed
  **0 open / 0 closed**. Neither this UI nor the independent history heuristics
  can prove that no provider credential exists; push protection does not
  sanitize earlier commits. CodeQL was not configured in the reviewed UI.

### Active caches and material outside reach

- The signed-in Actions cache page listed **six existing caches**:
  **three** scoped to `refs/pull/286/merge` and **three** to `main`.
  Their displayed keys were `setup-python`/Python 3.13 pip-cache keys;
  sizes were approximately 97 MB for the three PR cache entries, and
  97 MB, 7.2 MB and 58 MB for the three `main` entries. These are **cache
  listings only**: cached bytes have **not** been examined, authenticated or
  declared clear. No cache was deleted or modified in this review.
- Earlier historical workflow log/artifact scanning covered the inventories
  itemized below, but deleted/expired artifacts, unadvertised/unreachable
  objects, external attachments, forks and off-platform copies remain outside
  the available evidence. Keep their exclusion explicit rather than equating
  "not visible" with "safe".

### Ownership declaration and acceptance boundary

- The owner stated in the project conversation that the repository contains
  **no employer, client or third-party material copied without the required
  permission**, and that original materials are theirs subject to applicable
  third-party licenses. This is a **self-declaration**, not an independent legal
  opinion, contributor assignment audit, patent/trademark determination or
  verified license chain for all dependencies, models and datasets.
- No confirmed live credential exposure was established in the described
  bounded scan or current UI alerts. That is *not* universal security
  clearance. Uninspectable caches and deleted/off-platform records, account
  and provider credential validity, historical access changes, and independent
  IP/title checks are still **not fully cleared**.
- **Gate decision as of this record: PR #286 remains DRAFT and unmerged.**
  Passing feature-head CI is an engineering result, not an owner risk-acceptance
  or a waiver of the PR's original comprehensive security gate. Before merge,
  explicitly resolve or document owner acceptance of residual risk and review
  the final diff; after merge, verify the exact new-main project workflows
  and a fresh successful managed dependency-graph run. Do not claim full
  historic publication clearance or Step255 acceptance on this basis.

## Explicitly unfinished comprehensive gate

The completed historical log, artifact and discussion screening above supersedes
previous interrupted-sweep notes. The owner reviewed several administrative pages on 24 October 2026 as
recorded above, superseding the earlier signed-out-browser limitation for
those *specific* screens. Cached bytes, unavailable/deleted objects, external
attachments, broader account/provider secret stores, historical access
configurations and independent third-party-rights documentation are **not
fully cleared**. Neither scan proves the contractual ownership chain or
provider-side token validity.

PR #286 must remain unmerged under its original comprehensive gate until
remaining review evidence is supplied. Successful CI and synthetic-fixture
triage do not silently waive that gate. No keys were rotated, no history was
rewritten, no branches were deleted, and no visibility change was made here.

## Residual-risk gate decision — 24 October 2026

**Decision: HOLD PR #286 as draft; do not merge yet.**
The security engineering and owner-visible controls have meaningfully improved,
but the PR's original *comprehensive publication-clearance* condition has not
been fulfilled. The repository is already public; this decision does not mean
that the unverified historical material can be made private retroactively.
"Zero current security alerts" and "all CI green" are different claims from
complete historical exposure review.

### Risk register

| ID | Area | Evidence and uncertainty | Disposition / required next evidence |
| --- | --- | --- | --- |
| R1 | Retained GitHub Actions caches | Six setup-python pip cache **entries** were visible to the signed-in owner (three PR merge-ref and three main); only metadata was inspected. Cache bytes and historical inaccessible cache entries were not checked. | **Open.** Obtain authorized inspection or make a reasoned, documented cache-retention/deletion decision, understanding deletion will not undo any historic exposure. Do not assert clean cache contents. |
| R2 | Deleted, expired, unreachable or off-platform objects | Prior independent Git/object/log/artifact/issue screening covered the documented *retrievable* inventory. Deleted or inaccessible logs/artifacts, unreachable server-side objects, earlier clones/forks and external attachments are outside that evidence. | **Inherently bounded.** Record these as exclusions; recover specific identified material where possible and require explicit **owner residual-risk acceptance** for what cannot be recovered, not an assertion of zero exposure. |
| R3 | Provider/account credential inventory | Current GitHub Actions repository/environment secret and variable pages displayed no entries and secret scanning displayed 0 open/closed alerts. External provider credentials, personal access tokens, historically removed values and integrations beyond displayed settings were not audited. | **Open.** Owner inventories actually used providers, tokens, deployment services and accounts privately; revoke/rotate **confirmed** compromised credentials first. Never publish credentials or unredacted inventories in public issues. |
| R4 | Dependency vulnerability coverage and graph | **Resolved technically** in PR #288: strict UTF-8 manifest with 14 unchanged pins, plus successful new managed graph run 40101625658 on corrected main. | **Engineering closed.** Owner-only Dependabot alerts inventory still requires review and is not proven empty. |
| R5 | CI supply-chain and merge governance | Full SHA action pinning resolved in PR #287, current main 25/25 green. Main ruleset still mandates pull requests but **no required status-check contexts**; owner account controls remain outside this connector. | **Partially closed.** Keep manual exact-head/full-suite acceptance until owner configures stable required CI checks. |
| R6 | Intellectual-property chain and notices | Owner declares no unpermitted employer, client or third-party materials; a proprietary license notice exists. No independent contributor assignment, all-model/dataset/dependency license review, trademark audit or external legal opinion was performed. | **Open bounded ownership risk.** Retain owner declaration as such; verify third-party dependencies and any contributions before any contractual exclusivity or customer promises. Do not treat the notice as proof of entire title. |
| R7 | Deployed-system exposure | There are no configured GitHub deployment environments or self-hosted runners per owner UI. No actual externally hosted authenticated HTTPS pilot has been accepted. | **Explicitly deferred non-public product gate** in issue #242. It cannot be described as a deployed or customer-ready service and is not solved by PR #286. |

### What is complete, versus what is not

- **Reviewed and recorded:** advertised reachable Git history; targeted
  historical Actions logs and retained artifacts; issue/comment inventory;
  synthetic scanner regression tests; 24 existing CI workflows; current
  owner-view administrative controls; the owner's original-material
  declaration. Source-level findings were triaged as described above and
  **no live provider credential was confirmed**.
- **Not completed:** forensic examination of retained cache bytes; recovery
  of inaccessible/deleted/off-platform objects; independent authentication
  of external account/credential inventories; contractual IP chain; and
  final-main dependency graph recovery. None is silently treated as clean.
- **Do not perform destructive remediation without evidence:** no speculative
  history rewrite, cache deletion, blanket credential rotation, loss of
  licensed code or withdrawal of existing developer access.

### Release decision and owner authorization boundary

This record is an **assessment**, not a security certification. At the
observed checkpoint, insufficient evidence exists for the *original*
comprehensive publication-clearance assertion, so PR #286 must remain draft.
The owner can independently choose a **limited, explicitly bounded engineering
integration** in the future, but doing so requires a separate recorded
acknowledgement of R1–R6 and the consequences of the already-public history;
the generic instruction to continue project work does not constitute that
specific risk acceptance. Such a decision would **not** make uninspected
material "clean" and would not close external deployment issue #242.

Before any authorized merge: review exact PR code/diff, recheck its current
head and 24/24 feature-head workflows and backend logs, then verify applicable
PR requirements. After merge: confirm the exact resulting main SHA and
24/24 successful **push** workflows, inspect the full backend result, and
obtain a separate fresh successful managed dependency-graph validation.
At the original review time, Step255 PR #284 was unaccepted; the reconciled current checkpoint above records its subsequently verified successful merge.
