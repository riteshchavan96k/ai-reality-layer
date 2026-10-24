# AI Reality Layer — GitHub Actions immutable action pinning

## Scope (24 October 2026)

This non-product security change pins all three GitHub-provided reusable actions
referenced by the existing 24 CI workflows to **full 40-character commit IDs**.
The version tags are retained **only as explanatory comments** so source code
execution is determined by an immutable Git commit, not a movable tag.

| Action | Previously used tag | Immutable action commit |
| --- | --- | --- |
| actions/checkout | v7 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| actions/setup-python | v7 | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` |
| actions/upload-artifact | v4 | `ea165f8d65b6e75b540449e92b4886f43607fa02` |

These commits were resolved from the respective official GitHub repository
`git/ref/tags` API on 24 October 2026. They are not new action releases; this
patch is intended to retain the currently-used action code at that snapshot.
It does not upgrade or replace dependencies and does not alter the workflow
jobs, events, permission scopes, commands, conditions or artifacts.

## Independent acceptance requirements

1. Inspect the exact PR diff; only GitHub Actions `uses:` references and this
   note should change. Confirm every executable `uses:` is pinned to a full SHA.
2. Verify all 24 existing PR-head workflows complete successfully on the
   **exact latest head**. In particular, review real TLS/source/model jobs
   and the complete backend regression log.
3. Merge with standard protected-branch PR workflow only after the above and
   any independent security gates are satisfied. Independently verify all 24
   GitHub Actions `push` workflows on the final merged `main` SHA.
4. **Only after pinning is merged and validated**, the repository owner can
   consider setting GitHub Actions policy to require actions to be pinned to
   full SHA. Verify the policy does not exclude any necessary workflow,
   future action or trusted usage.

## Important exclusions

- Immutable action pinning mitigates movable GitHub Action tag supply-chain
  changes; it does not establish the action source code is harmless or
  completely eliminate risks from untrusted pull requests, third-party
  package resolution, transitive downloads, or malicious workflows.
- Review and update pinned SHA intentionally when adopting new action
  versions; do not silently switch back to tags.
- The default `main` ruleset does not yet require passing CI contexts
  automatically. Selecting stable required check names and enforcing them
  is an owner-only configuration task after tests prove stable.
- This work is **independent of security review PR #286**. It does not
  establish its comprehensive history/privacy/ownership clearance, fix
  the managed dependency graph on `main`, or accept product Step255.
