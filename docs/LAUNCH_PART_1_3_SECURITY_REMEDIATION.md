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


## Current evidence checkpoint — 24 November 2026

This checkpoint supersedes older chronological statements about whether the Dependabot and secret-scanning screenshots were verified. It **does not** convert owner-only or deployment gates into completed acceptance.

### Verified current repository state

- Accepted `main`: `0116a9dda1df961d25f60bef5bf9886f23e1afb9`.
- GitHub API reports **31 check-run records** for this exact SHA; all are `completed / success`. The required protected-main contexts remain `Python 3.13 full suite` and `Real official publisher heldout + optional pinned model` under active ruleset #25773872, with no bypass actors.
- [PR #295](https://github.com/riteshchavan96k/ai-reality-layer/pull/295) merged the four dependency fixes. Owner-provided authenticated Dependabot screenshot shows **0 open / 4 closed**, with the four alerts marked **Fixed**. Patched pins include `pytest==9.0.3` and `pyarrow==23.0.1` in their affected non-production manifests.
- Owner-provided **unfiltered** Secret scanning screenshot shows **0 open / 0 closed**. Separate Advanced Security screenshot shows **Secret Protection enabled** and **Push protection On**.
- The weekly production Python dependency advisory workflow ran successfully on **23 November 2026** (run [45195839522](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/45195839522)); the preceding weekly runs on 2, 9 and 16 November also succeeded. This checks the resolved production Python package closure against the configured PyPI advisory service. It is not a container OS scan, legal clearance, or guarantee against unknown vulnerabilities.
- Production requirements remain strictly pinned and separate from development / optional ML benchmark dependencies. The dependency guard checks the Dockerfile installs only `backend/requirements.txt`.

### Cache workflow review (configuration only)

The reviewed backend CI uses `actions/setup-python` pip caching keyed to `backend/requirements.txt` and `backend/requirements-dev.txt`; the workflow declares `permissions: contents: read`. The production dependency audit uses `pip --no-cache-dir`. The inspected workflows do not use a direct `actions/cache` step.

Historical owner screenshots from 24 October 2026 showed **six entries (three on `main`, three on PR #286 merge refs), all identified as Python pip caches**. This is a dated snapshot only; it does not establish the current count, actual bytes, keys, last-used metadata, or content safety. No cache was deleted.

**Actual retained cache inventory and bytes remain unverified.** The connected GitHub integration cannot read the owner-only Actions cache listing; the owner must review Actions → Caches and record a private retention/invalidation decision. Prior documentation of a six-cache snapshot is historical, not a current count.

### Remaining objective blockers

1. **Owner cache review:** inspect current cache entries, branch/ref scopes, provenance and last-used metadata; retain or expire/invalidate with reason. If a credential is suspected in cache, revoke/rotate it at the issuing provider before relying on cache deletion.
2. **Owner credential/access review:** inspect personal GitHub PATs, OAuth/installed Apps, deploy keys, collaborators, webhooks, repository/organization Actions secrets and variables, plus every external cloud/model/API provider and old development environment. Do not paste secrets or inventory details into chat or public issues. Record only a private redacted completion/remediation attestation.
3. **Rights/provenance review:** review actual first-alpha service/runtime and any distributed material, contributions/employer/client ownership, source terms, optional model/dataset and SDK rights if used or distributed. Publisher metadata is not a legal rights determination.
4. **Bounded historical exclusions:** owner records what could not be inspected (unreachable/deleted Git objects, expired logs/artifacts, off-platform clones/stores) and explicitly accepts or rejects the residual risk for the narrowly restricted alpha. Do not claim exhaustive clean history.
5. **Container image hardening:** current Dockerfile uses mutable `python:3.13-slim`, runs as UID/GID 10001 and disables pip cache, but the base image is **not pinned by digest** and the built image/OS layer has **not had an independent vulnerability scan**. Resolve a reviewed digest, build the exact image, scan it, and remediate or document applicable findings before hosted pilot acceptance.
6. **External pilot release gate:** Issue #242 remains open. TLS ingress, no direct public port 8080, managed bearer secret, ingress rate/body/concurrency/time controls, egress boundaries, monitoring, budget, rollback, and independent external HTTPS client probes must be verified on the actual host. Passing CI/local Docker does not complete this gate.

### Current acceptance decision

**Repository-side evidence review is substantially complete; Launch Part 1.3 overall security acceptance remains OPEN.** No owner-only credential, cache, rights or historical residual-risk decision is inferred from screenshots, tests or documentation. No external customer API is authorized by this checkpoint. Continue only with bounded, restricted-alpha preparation until the owner-only reviews and mandatory external pilot gate have evidence.
