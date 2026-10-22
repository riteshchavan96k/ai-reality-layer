# AI Reality Layer - Prepublication Security Gate

STATUS: NOT CLEARED FOR PUBLICATION. This is a mandatory process,
not proof of a clean codebase or guaranteed exclusive IP rights.

## Verified scope at start

Repository owner: riteshchavan96k (administrative access confirmed).
Main prior accepted Step254: a99d8cfdb60324187b6142f97e001b082328f7a6.
Draft Step255 PR #284 stays separate. Existing 24 workflows did not
run for the Step255 PR because GitHub Actions private minutes/billing
prevented runner allocation. Nothing here authorizes bypassing CI.

The current main Git tree contains no filenames matching selected .env,
private-key or local-database patterns. Selected current sensitive code,
workflows and historic commit patches did not reveal a high-confidence
literal key signature. THIS IS NOT A FULL HISTORY OR LOG AUDIT.

This branch adds a root proprietary All Rights Reserved license, stronger
.gitignore credential patterns, and a read-only history auditing script.
Ignore rules do not erase any historic commits.

## Required steps BEFORE converting private to public

1. From a trusted authenticated developer workstation, create a complete
   new Git mirror: git clone --mirror
   https://github.com/riteshchavan96k/ai-reality-layer.git
   ai-reality-layer-audit.git

2. From a checkout containing this branch's scanner execute:

   python scripts/prepublication_history_audit.py
   ai-reality-layer-audit.git > private-audit.json

   This scans reachable Git object blobs, includes deleted historical files,
   prints finding categories, blob IDs and paths, but not actual secret
   values. Keep the entire private report off public GitHub and out of PR
   discussions. Scanner exit 0 never means publication was approved.
   Also run a vetted maintained independent tool (e.g. TruffleHog) locally.

3. Separately audit all branch, tag and pull-request heads (some refs are
   excluded from a normal mirror), GitHub Actions historical logs, caches,
   artifacts, PR discussions, issue attachments and releases. Making the
   repository public exposes its Actions history and logs. Inspect account
   secret stores and collaborator permissions in authorized GitHub Settings.

4. On a VERIFIED leaked credential, REVOKE OR ROTATE AT ITS PROVIDER FIRST,
   investigate any unauthorized access, and prevent continued use. If
   history rewriting is still justified, coordinate a freeze, backup and
   precise filters with the owner. Use a current git-filter-repo release
   with --sensitive-data-removal on a disposable mirror, inspect the rewritten
   refs and coordinate cleanup of old clones, forks and GitHub PR caches.
   NEVER run blanket force pushes or rewrite history speculatively.

5. Audit all third-party licensing, model/dataset licenses, ownership
   assignments, contractual duties, and potential confidential material.
   Git commit authorship alone cannot certify ownership. The project is
   NOT under an open-source license; a public GitHub repo can still be
   forked through GitHub platform functionality.

6. After remediations, rerun full-history scanners, confirm findings have
   been resolved and have the owner review the full report, past logs and
   ruleset settings. The owner may then authorize public visibility.
   GitHub warns that push rulesets may be disabled on conversion.

## Unresolved release blockers

- Full remote history blob scan not performed through available linked tools.
- Old Actions logs, PR refs and artifacts not fully cleared.
- Account-wide credentials, roles and third-party IP not independently cleared.
- No compromised secret verified; no keys rotated; no history rewritten.
- Automated CI still unavailable until account billing/quota permits it.

Stop here until those are addressed. Step255 should not be merged without
independently successful PR and exact merged-main workflows.
