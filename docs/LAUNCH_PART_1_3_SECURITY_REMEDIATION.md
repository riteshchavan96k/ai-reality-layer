# Launch Part 1.3 — production dependency remediation and owner-only risk acceptance

**Date:** 27 October 2026. **Starting accepted `main`:** `0ba1e85e0a638f9ebda378be233786674f9cbda7` (Part 1.2 / PR #292).

## Purpose and limits

Reduce real pre-alpha software-supply-chain risk, identify whether the pinned production dependency closure has *reported known* Python-package vulnerabilities, and make the remaining private security decisions explicit. This part does not claim legal/forensic clearance or authorize a public deployment. Product functionality remains Step 255. The restricted authenticated HTTPS deployment is still **not accepted** under [Issue #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242).

The historical audit [PR #286](https://github.com/riteshchavan96k/ai-reality-layer/pull/286) remains **draft/unmerged**. The earlier 'no required checks' finding was resolved under [PR #291](https://github.com/riteshchavan96k/ai-reality-layer/pull/291) and Issue #290.

## Engineering risk reduction added in this part

- New GitHub Actions workflow `.github/workflows/launch-production-dependency-audit.yml` runs on `pull_request`, `main` push, an explicit manual trigger, and weekly schedule. No repository secrets or write privileges are requested; checkout/setup-python refs are immutable commit SHAs.
- `scripts/launch_production_dependency_guard.py` refuses empty, duplicated, floating, remote, or nonstandard production manifest entries. It confirms the release Dockerfile installs the expected **production-only** `backend/requirements.txt`, not dev/benchmark/ML extras.
- Independently install the actual resolved runtime requirements into an isolated Python 3.13 virtual environment, check dependency metadata compatibility with `pip check`, then produce an exact `pip freeze` snapshot of that environment. This is not a Docker-image or OS vulnerability scan, and must be repeated against the real built image before launch.
- Independently pinned `pip-audit==2.10.1` checks the frozen installed Python closure against PyPI's published vulnerability database with `--strict --no-deps --disable-pip`. The check **fails** for advisories or unsuccessful audit collection, has no ignored vulnerability IDs, uses no suppression, and does not modify package versions. A successful run means **no known advisories were reported for that installed closure at the time**, not that all bugs are absent.
- The installed runtime prints direct-dependency `License-Expression` / `License` / license classifier metadata for private owner follow-up. These are **self-declared metadata, not a license-use determination**. The root proprietary `LICENSE` cannot override third-party conditions. The optional pretrained models, datasets, dev packages and downstream distributed SDK rights are not cleared by a Python runtime dependency inventory.
- New offline Python tests guard pin uniqueness, exact versions, source restrictions, and Docker production scope. No application runtime behavior or production dependencies are altered.
- This new advisory workflow is **independently informative**. It is **not yet one of main's two admin-configured mandatory checks**. A passing PR and passing application CI cannot be called alpha release-ready if the release advisory scan or independent Docker/image scan has an unresolved actual vulnerable package.

## Outstanding risk register / owner-private disposition

| ID | Actual evidence | Required private action | State |
| --- | --- | --- | --- |
| L13-C1 | Previous documented history scans had no *confirmed* live leaked provider token in their bounded triage; current repository tree filenames were screened in Part 1.2. No tool can certify unreachable files/secret-store contents. | Review personal-access tokens, GitHub app permissions, external LLM/cloud/service credentials and previous private development environments. Revoke or rotate only identified exposed/stale credentials. Record **redacted** inventory completion and any material remediation outside public GitHub. | **OWNER-ONLY / NOT VERIFIED** |
| L13-C2 | Historical signed-in UI listed six setup-python/pip Actions caches. Their actual bytes and later cache changes have **not** been examined. | GitHub → Actions → Caches: privately inspect count, creation, scopes and provenance. Decide keep/expire/invalidate; if a real token was ever cached, revoke at provider first. Record decision without leaking filenames/values. | **OWNER-ONLY / NOT VERIFIED** |
| L13-C3 | Dependency-graph UTF-8 encoding was repaired in PR #288 and previously generated successfully. Full current Dependabot alert inventory is not exposed via the connected app. The new workflow independently audits the **installed Python closure**, not container/OS libraries. | GitHub → Security → Dependabot alerts and Secret scanning: inspect all open/closed filters and severity. Remediate meaningful hits. Before hosting, run a trusted full built-container/base-image vulnerability audit with an approved image digest and document remediation. | **OWNER/RELEASE GATE** |
| L13-C4 | Proprietary root LICENSE and direct-dependency metadata exist; no independent ownership/rights chain is proven. | Privately check employer/client contributions and source ownership, direct/runtime dependency license obligations, any distributed code/SDK, official Python.org page-use rules, optional Hugging Face model weights/dataset terms if ever shipped. Seek legal review for unclear facts. | **OWNER/RIGHTS REVIEW** |
| L13-C5 | Deleted/expired GitHub artifacts, unadvertised Git objects, historical off-platform clones and personal provider stores cannot be recovered exhaustively. | Record specific known exclusions and a *bounded*, explicit owner risk decision. No blanket claim of zero prior exposure; do not rewrite history or delete caches speculatively. | **OWNER DECISION** |
| L13-C6 | Protected main requires both official CI checks; merged PR #291 demonstrated failing PR blocked and passing PR accepted. | Preserve ruleset #25773872. Optionally require the new audited job after its name/stability is verified, without guessing its context or disrupting release engineering. | **CI MERGE GATE CLOSED; NEW AUDIT ADVISORY PENDING** |
| L13-C7 | No actual external hosted, independently verified, TLS-protected AI Reality Layer service exists. | Keep [release gate #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242) open. Apply managed credentials, ingress rate limits, source egress controls, logging, resource/cost limits, rotation and independent client probes. | **HARD RELEASE BLOCKER** |

### Private owner verification (do not send secrets into chat or public issues)

1. Open repository **Security → Dependabot alerts** and **Secret scanning** and review filters; record only counts/severity/remediation status. Also review enabled push protection.
2. In **Actions → Caches**, review the current caches, origins and whether existing historical entries are needed. Do not claim bytes were scanned; do not delete or rotate keys without justified authorization.
3. In **Settings → Secrets and variables**, **Collaborators**, **Deploy keys**, **Webhooks**, and **Installed GitHub Apps**, review access. Separately check GitHub PATs and any external providers. Record private attestations, not tokens.
4. For any genuine flagged vulnerability or uncertain license, identify the *exact affected shipped artifact and exposure*, apply a testable bounded fix, and recheck the protected PR and **exact new `main`** workflows.
5. Before external customer access, sign off privately on the scope and residual risks, and confirm Issue #242's actual deployment gate independently. A repository test cannot stand in for an operator's own review.

## Acceptance definitions

**Engineering acceptance:** Manifest/Docker guard and unit tests passed, new no-secret audit workflow executed successfully on the reviewed PR and *exact merged main*, no unfixed known advisory in the measured runtime closure, and full historical CI preserved. Document any genuinely observed advisories instead of hiding them.

**Full owner security clearance:** **Not complete until** owner-only account/credential/cache/rights review and bounded risk decisions have actual evidence. It may not be inferred from merge. This document must not mark Launch Part 1.3 **fully complete** on the user's behalf.

**Deployment:** Never call this an externally deployed or customer-ready product. Hosting remains subsequent launch work; Step 255 remains the accepted product milestone.
