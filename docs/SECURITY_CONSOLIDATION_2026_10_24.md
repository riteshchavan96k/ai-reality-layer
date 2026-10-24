# AI Reality Layer — actionable security consolidation (24 October 2026)

## Purpose and acceptance boundary

This focused engineering integration extracts only the reviewed,
non-destructive safeguards from draft
[security PR #286](https://github.com/riteshchavan96k/ai-reality-layer/pull/286).
It **does not** merge or waive that PR's separate historical-security and
ownership-risk assessment. Current accepted product baseline remains
[Step 255](STEP_255.md) on protected `main` at
`5239de5f34dff3bd362f90b11189677235b3467c`, with 25/25 push workflows
and 3,348 backend tests passing. The final SHA for this **new** security
consolidation must be independently validated after its own merge.

## What is integrated

- Additional `.gitignore` patterns for local/nested `.env` files, private
  keys, credential/secret JSON, pip and application configuration, local
  databases and private scanner output. **Ignore patterns do not remove
  data already committed to Git or stop deliberate `git add -f`.**
- Read-only `scripts/prepublication_history_audit.py` requiring a complete
  trusted Git mirror to screen reachable blobs, commits, tree paths and tags
  with redacted potential-finding locations. Sensitive *values* are not
  emitted in normal JSON results; operator must privately triage findings.
- The five reviewed synthetic history scanner regressions plus an additional
  test verifying that representative sensitive filenames are ignored while
  normal project files remain unaffected.
- Milestone documents synchronized to exact Step 255 acceptance without
  changing its product APIs, model weights, dependency pins or benchmark.
- Old managed GitHub dependency-graph UTF-16 issue fixed separately by
  [PR #288](https://github.com/riteshchavan96k/ai-reality-layer/pull/288):
  14/14 dependency pins preserved and fresh managed graph run
  [40101625658](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/40101625658)
  succeeded. Mutable action tags were independently pinned in
  [PR #287](https://github.com/riteshchavan96k/ai-reality-layer/pull/287).

## Explicit outstanding security matters

**PR #286 stays DRAFT and UNMERGED** unless its own gate is separately
resolved or the owner explicitly accepts a bounded residual-risk decision.

1. **Reachability:** deleted/expired/unreachable Git objects, past artifacts,
   external attachments and copies are not reliably inspectable.
2. **Caches:** earlier owner UI listed six existing pip caches, but neither
   their complete bytes nor earlier inaccessible cache contents were audited.
3. **Credentials:** absence of GitHub repository secrets and current scanner
   alerts is not proof about other providers, revoked or past tokens, or
   account-level secret locations. Never print actual secrets in public issues.
4. **Rights:** the owner's declaration and proprietary LICENSE do not
   independently prove every third-party model, dataset and contribution
   satisfies its applicable rights and licenses.
5. **Policy controls:** GitHub `main` ruleset currently requires a PR and
   blocks force push/deletion, but has **zero mandatory CI status checks**;
   the GitHub app cannot administer rulesets. An authorized owner should
   configure stable required checks only after confirming GitHub UI captures
   the correct check names and compatible runner permissions.
6. **Operational deployment:** restricted external HTTPS pilot
   [issue #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242)
   remains OPEN and must block **customer-ready** or **deployed** claims;
   it does not prevent further nonpublic, rigorously tested engineering.

The separately managed Dependabot alert inventory is also account-restricted.
A successful dependency-graph submission **does not** assert zero vulnerable
packages; the owner should recheck Security → Dependabot alerts after recovery.

## Reproducing limited, non-clearance scan

Create a **trusted, full, non-shallow mirror** and include all advertised
branch, tag, and PR references. A scan of a plain GitHub checkout without
full history or a working tree is insufficient to declare historical safety.

```shell
git clone --mirror https://github.com/riteshchavan96k/ai-reality-layer.git ai-reality-layer-audit.git
git -C ai-reality-layer-audit.git fetch origin '+refs/pull/*/head:refs/pull/*/head' '+refs/pull/*/merge:refs/pull/*/merge'
python scripts/prepublication_history_audit.py ai-reality-layer-audit.git > private-audit.json
python -m pytest -q backend/tests/test_prepublication_history_audit.py
```

Review output privately; the scanner always returns
`"publication_cleared": false`, even with no heuristic matches. Retain
scanner output outside the repository; delete no Git history or caches
without evidence and deliberate authorization. No ongoing monitoring,
external deployment or owner risk acceptance is implied by this note.
