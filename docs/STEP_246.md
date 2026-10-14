# Step 246 — opt-in temporal original-source recheck, not autonomous monitoring

## Verified previous milestone and genuine scope

On 15 October 2026, independently checked actual GitHub main
`2e3061627329cbd3f0b73f9ed018ac42ec93c7ed`. Accepted Step245
was implemented through PR #272 and documented through PR #273.
All **19/19 push-triggered GitHub Actions** were successful on that exact
main SHA; full backend regression 2,936 passed. Latest accepted workflow
lets a developer safely inspect a current single or two-host original-source
claim via an opt-in local CLI. There was no existing Step246 specification.

**Observed practical limitation:** a developer still cannot directly recheck
the SAME claim against the SAME official HTTPS source and compare an earlier
bounded capture with a fresh one. AI Reality Layer must address changing
real-world observations rather than only offer a one-time static result.
Step246 provides this missing bounded temporal re-observation capability.
It does not infer semantic truth or claim that the historical receipt is
cryptographically authenticated.

## Real implementation

- New `backend/app/integrations/source_recheck.py` exports
  `recheck_cited_answer_with_api(client, token, validated_request, previous)`.
  `previous` must be a previously consumed `ClientCitedAnswer` from the
  existing Step242 client. Validate request-binding SHA256, source identity,
  immutable typed source citation, exact quote SHA256, capture hash shape,
  UTC observation time, stable source quote grammar and bounded claim
  relation, fixed decision/answer, and literal false epistemic ceilings.
  Invalid baseline returns abstention **before making any source request**.
- Make exactly ONE fresh authenticated Step241 cited-answer POST, using the
  existing Step242 client and its strict fresh source/capture/quote gating.
  The server independently reads the same exact operator-approved HTTPS URL.
  A comparison is only successful when **both** bounded observations pass:
  (1) same capture digest and same bounded statement/decision =>
  `capture_unchanged`; (2) different capture digest, same quote and decision
  => `capture_changed_statement_unchanged`; (3) different capture digest,
  different quote or decision => `bounded_statement_changed`.
  If identical raw-byte digest has inconsistent quote or decision,
  a fresh observation is older than the prior, or any check fails, return
  `abstain` with **zero source citations** and no leaked partial receipts.
- A baseline can be old and is valid only as a **comparison baseline**,
  never as currently fresh evidence. The current source must independently
  satisfy request freshness. Change detection is on captured byte SHA256,
  source-text quote SHA256 and narrow grammatical relationship; it does NOT
  prove that the factual truth or publisher's statement objectively changed.
- Extend the runnable `python -m backend.app.cli` with
  `--recheck` **only for a single exact operator-approved source URL**,
  requiring `--live`, pilot bearer environment and current allowlist as
  in Step245. The CLI intentionally makes two sequential authenticated
  independent source captures in the same run: prior and re-observation.
  The Python client API separately supports delayed rechecks if a trusted
  developer application retains an earlier **validated in-memory** result.
  This milestone intentionally provides **no automatic scheduling,
  historical persistence or third-party attestation service**.
- The safe JSON output includes the classification, bounded prior and
  current decisions, capture hashes, quote hashes and observation times
  **only if both** succeeded. Untrusted raw original-source quotes are
  hidden unless an operator explicitly adds
  `--include-untrusted-quotes`; never render them as HTML or system prompts.
  All factual truth, signed history, independent publisher ownership and
  automatic-monitoring claims remain false. CLI exit 0 signals complete
  bounded comparison, NOT objective truth; 2 is abstention, 3 refusal.
- Dedicated adversarial tests use **MOCKED** source snapshots for
  digest-only changes, bounded statement change to contradiction,
  reverse transition, stale/quoted/irrelevant source, mismatched capture,
  forged prior receipt/claims, early refusal, no opt-in, unsupported two-host
  recheck, no credentials/errors leaked. All legacy endpoints stay intact.
- New twentieth GitHub Actions workflow runs those tests and a **genuine**
  fixed official Python.org historical release page HTTPS twice via the
  local authenticated client and CLI, checking either unchanged capture or
  changed raw capture with unchanged bounded quote. This establishes that a
  real operator can compare *two current live observations*, not long-term
  history, publisher authority, or external production reliability.

## Reproduce the local command

Configure current local operator pilot settings (Step231 and Step245):
`ARL_RUNTIME_MODE=pilot`, printable secret environment
`ARL_PILOT_BEARER_TOKEN` (32–256 chars), and approved exact source URL in
`ARL_INDEPENDENT_SOURCE_ALLOWED_URLS` JSON. Do not put the token in argv.
From repository root:

```sh
python -m backend.app.cli --live --recheck \
  --claim "Python 3.13.0 is a stable release." \
  --entity "Python 3.13.0" \
  --source "https://www.python.org/downloads/release/python-3130/"
```

To compare at a later time from a trusted developer app, retain the
immutable `ClientCitedAnswer` returned from
`check_cited_answer_with_api` and call
`recheck_cited_answer_with_api(client, token, request, old_answer)`.
Historical dataclasses are **not MACs or signatures**; without a separately
trusted history store the application cannot prove when a baseline was
really captured. This is an explicit limitation, not automatic provenance.

## Security, trust and acceptance criteria

Original source byte hashes do not authenticate publisher authorship,
and two captures do not prove real-world factual truth. The same HTTPS
origin is operator-pinned and protected against private-IP/dangerous
redirect access by pre-existing backend reader. No arbitrary web search,
agent actions, ML promotion, bearer-token logs, unbounded retries or public
HTTPS deployment. No real two-independent-publisher corroboration is
claimed; deferred Step234 external release remains on hold and open
GitHub release gate issue #242 is not engineering Step242.

Do not mark Step246 ✅ until the feature PR is merged, the old backend
suite and new adverse tests and actual Python.org twice-captured canary
all pass, and **every 20 GitHub Actions push workflow succeeds on the
exact FINAL main SHA**. Any acceptance-documentation merge creates another
main SHA requiring fresh 20/20 CI. Record final acceptance via PR audit
comment without a later unverified commit.
