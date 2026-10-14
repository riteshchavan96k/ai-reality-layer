# Step 245 — genuine local operator claim-check CLI using existing verified AI Reality Layer clients

## Repository-verified predecessor and real product gap

On 15 October 2026, independently checked actual main SHA
`5dfcc73e753953741ac63b3573933816460b9d05`.
Step244 is the latest completed engineering milestone (implementation PR270,
acceptance PR271). **All 18 GitHub Actions push workflows succeeded on
that exact final SHA**; backend suite had 2,910 passing tests, including 70
Step244 defensive app consumer cases, and the genuine Python.org+IANA HTTPS
two-host client canary correctly abstained with unrelated IANA content.
No preexisting Step245 specification was present.

**Observed practical product gap:** despite genuine authenticated source
observation and audited SDK functions for one or two sources, a new AI
developer/operator could not yet invoke a complete real claim-checking workflow
as a reusable command without writing integration code. That reduces actual
testability/usability of our startup's current infrastructure. Introducing
broad semantic claim support or pretending that two hostnames certify truth
would be unjustified; a runnable, explicitly bounded local operator workflow
is the next testable product addition.

## Implemented functionality and use

- Adds `python -m backend.app.cli`. The operator submits
  `--claim`, `--entity`, one or two `--source` values,
  `--max-age`, and **explicit `--live`**. No network request is
  permitted without explicit consent, valid pilot configuration and every
  exact requested URL already in the server allowlist. No arbitrary web
  search or multi-hop URL selection.
- Uses only existing server-side original-source reading, pilot bearer
  middleware and Step242/Step244 fail-closed application clients, through
  an in-process authenticated FastAPI `TestClient`, not external hosting.
  One allowed source yields fixed bounded alignment/contradiction/abstain
  plus a vetted citation; two allowed distinct-host sources yield bounded
  alignment/contradiction/disagreement/abstain with zero partial citations.
  Does not invent semantic reasoning or retry denied original URLs.
- Requires `ARL_RUNTIME_MODE=pilot`, a high-entropy printable ASCII
  `ARL_PILOT_BEARER_TOKEN` in the operator's environment, and the
  existing `ARL_INDEPENDENT_SOURCE_ALLOWED_URLS` JSON exact allowlist.
  **Bearer tokens are NEVER accepted as argv or printed**. Pilot settings
  and all URLs are preflighted before source egress. The CLI is strictly
  local and binds no public server port.
- Outputs one line of machine-readable JSON with bounded decision,
  reason code, fixed safe text, source observations only when citations
  survived the trusted SDK validators, claim-request binding SHA256, and
  unchanging literal `factual_truth_verified=false`, publisher-authorship,
  independently-owned publisher, neural and general-QA ceilings. A
  source contradiction/disagreement is NEVER treated as permission to claim
  support or objective truth.
- Original source quotations are **omitted by default**. Their original
  text is included only with `--include-untrusted-quotes` as JSON DATA
  requiring escaping before HTML UI display. Quotes must not be executed
  or interpolated into model system prompts. Source metadata is also
  completely absent when the source verification abstains.
- Exit status: 0 for complete bounded source observations (including
  source contradiction/disagreement; `may_use_as_bounded_evidence` is the
  separate evidence-permission signal), 2 for abstention, 3 for refused
  invalid/unapproved/disabled requests, 4 for unhandled local failures.
  Do not use exit code 0 as a categorical truth signal.
- Adds adversarial authenticated FastAPI/CLI tests for single support,
  contradiction, two mocked support/contradiction/conflict conditions,
  partial/stale source refusal, invalid tokens/runtime, SSRF-shaped
  URLs, invalid source counts/freshness, off-allowlist early block,
  no-network without --live, no leaked secrets, no accidental original
  quotes, one-line JSON, and no unsupported semantic promotion.
- Adds nineteenth GitHub Actions workflow plus **genuine** opt-in
  Python.org historical release-page HTTPS → authenticated local API →
  command output of a narrowly observed source citation. The same live
  run must abstain when a second unrelated IANA page is required, reject
  off-list source and missing --live before any network. **This is a usable
  actual developer workflow**, not claimed as production deployment.

## Operator usage (locally only)

Operator must provide these variables via secure local configuration
(no actual token or secrets committed):

- `ARL_RUNTIME_MODE=pilot`
- `ARL_PILOT_BEARER_TOKEN` = randomly generated printable ASCII bearer,
  32–256 chars (never passed on CLI command line).
- `ARL_INDEPENDENT_SOURCE_ALLOWED_URLS` = JSON array of exact approved
  HTTPS URLs, such as the specific official Python release page below.

Then execute:

```sh
python -m backend.app.cli \
  --live \
  --claim "Python 3.13.0 is a stable release." \
  --entity "Python 3.13.0" \
  --source "https://www.python.org/downloads/release/python-3130/" \
  --max-age 3600
```

Or add a second source:

```sh
python -m backend.app.cli \
  --live \
  --claim "Python 3.13.0 is a stable release." \
  --entity "Python 3.13.0" \
  --source "https://www.python.org/downloads/release/python-3130/" \
  --source "https://www.iana.org/domains/reserved"
```

The unrelated IANA site must lead to **abstention** and **zero citations**.
The CLI does not modify the operator allowlist, configure tokens itself,
perform open-web discovery, or auto-enable deployment. Avoid shell history
for credentials: keep bearer out of argv entirely. CLI output and source
citations can be saved only under operator-approved data handling rules.

## Limits

- The server and client still use the same narrow bounded literal atomic
  assertion grammar. Historical Python.org document presence is
  *textual source evidence* and not factual-truth assurance.
- Two HTTPS hostnames do not establish independently owned/editorially
  independent publishers; SHA-256 receipts do not authenticate publisher
  authorship or guarantee a page is true. No verified real two-site
  positive corroboration, broad NLI reliability, model/agent autonomy,
  source discovery, semantic general-QA, customer validation or production
  security is claimed.
- `TestClient` is an intentional **local** integration transport; it
  is not publicly reachable HTTPS deployment. Owner-deferred Step234
  external release remains deferred, and the mandatory open release
  issue #242 is a release gate, not engineering Step242.

## Required acceptance before any completion checkmark

Do not mark Step245 complete until feature PR is merged, all existing
regressions and the new CLI adversarial + genuine HTTPS tests pass, and
**all 19 GitHub Actions `push` workflows on the exact final accepted
`main` SHA** finish success. If there is a documentation-sync merge
after implementation verification, it changes main and requires another
19/19 exact-SHA full verification. Record final accepted SHA in the PR
thread without creating a later unverified commit.

## Independently verified implementation acceptance (15 October 2026)

- [PR #272](https://github.com/riteshchavan96k/ai-reality-layer/pull/272)
  merged into `main` SHA `5220ef5da7cdf4637acffb3a0c9e7206094bd936`,
  with all 19 GitHub Actions `push` workflows independently checked as
  `completed/success` on exactly that SHA (not PR-only checks).
- Full regression [run 38629937439](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38629937439),
  job `116078674045`, inspected job log: **2,936 passing tests
  in 10.23 seconds**, including 26 new Step245 tests.
- Operator CLI [run 38629937757](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38629937757),
  job `116078674671`, inspected job log: **26 passed in 0.64s**;
  genuine Python.org source capture -> authenticated local FastAPI ->
  bounded observed source citation in operator CLI. Same runner also made
  genuine Python.org + IANA HTTPS two-host observations which **abstained
  without partial source evidence**, and verified no `--live` and
  off-allowlist fail before source egress, without credentials/raw text logged.
- Single-source live citation is a verified original-source text observation,
  not publisher-signed authorship or objective truth. Dual-positive and mixed
  local API tests use deliberately mocked source bodies. No broad semantic
  factual accuracy, independent publisher ownership, public deployment or
  customer field evaluation has been performed.
- **Step245 implementation scoped engineering is accepted ✅ on this
  independently checked implementation SHA.** Final acceptance docs merge
  creates another SHA and must pass all 19 push CI workflows on the exact
  final main revision before closing Step245. Record that final SHA and
  its job logs on acceptance PR without further code/README edits.
