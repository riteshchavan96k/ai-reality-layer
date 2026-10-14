# Step 244 — fail-closed two-origin comparison client for AI developer applications

## Repository verification and scope

On 15 October 2026, independently refetched GitHub main commit
802472760d8be47239f2336de0be413d98212ad2. Step 243 is the latest
accepted engineering milestone, merged through PRs #268 and #269;
17/17 Actions PUSH workflows completed success on precisely that final main.
Full backend: 2,840 tests passed, including 26 Step243 adversarial tests.
Step243 live Python.org plus IANA HTTPS correctly abstained on unrelated
second source. There was no prior Step244 specification in the repository.

Step243 delivered an authenticated two-source comparison API, but no
developer application consumer capable of independently validating the two
citations and protecting a calling AI against misbound, forged, rehashed,
stale or contradictory source receipts. Step242's client only validates a
single original-source cited answer. Filling that real usability gap, without
inventing a more capable semantic verifier, is the justified Step244 scope.

## Scoped functional implementation

- Add backend/app/integrations/two_origin_answer_client.py exposing
  check_two_origin_answer_with_api(client, token, request) for one deliberate
  authenticated POST to /api/v1/reality-state/answer/compare and
  interpret_two_origin_answer(data, request, now=None) for independent
  offline validation. The caller must supply a trusted API transport and
  securely configured bearer. No source URLs are independently fetched
  by the consumer; no models, no autonomous operations or URL discovery.
- Verify Step243's canonical SHA256 pair request binding (source ORDER,
  claim, entity and freshness); full strict response schema; literal JSON
  booleans for every epistemic ceiling, pair evidence permission and
  distinct-host indication; exact outcome/reason/fixed answer-text mapping.
- Treat two citations as an indivisible unit. Require exactly two, in the
  specified source-URI order, with a bounded single-line exact original
  quote, UTF-8 quote SHA256, well-formed capture SHA256 and UTC
  server observation times within the requested freshness bound and at
  most 30-second future clock skew.
- Independently parse the narrowly allowed atomic claim and each
  observed quote using the Step227 grammar, recompute their alignment or
  contradiction, and reject a server/intermediary report of agreement
  when a citation demonstrably contradicts the submitted claim (even if
  the attacker rehashed that quote correctly). Mixed relations must be
  surfaced explicitly as source_disagreement; may_use_as_bounded_evidence
  is false for every result other than exact complete two-source alignment.
- Return immutable ClientTwoOriginAnswer and a tuple of immutable
  CitedSourceObservation objects ONLY if both source observations pass all
  validation. An invalid, partial, expired, stale or misattributed response
  returns a fixed abstention with NO URLs, quotes, capture hashes, timestamps
  or other partial citation.
- Reject malformed bearer credentials before any API call, malformed
  content types, non-JSON replies, HTTP errors, body over limit, thrown
  transport errors or partial source receipts; never echo untrusted errors
  or secrets.
- Add adversarial FastAPI + client tests, real producer positive (MOCKED
  original-source captures), contradiction, both disagreement orientations,
  stale/quoted/malformed/off-list/unauthorized refusals, immutable fields,
  exact request binding, rehashed fake alignment, and prior Step242 client
  compatibility.
- Add eighteenth GitHub Actions CI workflow: Step244 focused regression
  and opt-in Python.org plus IANA genuine HTTPS -> authenticated local
  FastAPI -> fail-closed downstream comparison consumer. IANA is unrelated
  to the Python release statement: the REAL canary's expected and required
  result is abstention with zero partial source citations; reversed order,
  invalid bearer and off-list source must not bypass the guard.

## Security and epistemic limitations

SHA256 is an unkeyed text-integrity receipt, NOT cryptographic proof of
publisher authorship or honest API origin. Caller must authenticate the API
transport using properly verified TLS when externally deployed. Two
different HTTPS hosts do NOT prove independent publisher ownership.
Observed source agreement does not prove real-world factual truth or
publisher independence. The client recomputes only conservative atomic
textual relationship; it does NOT verify that a hostile server supplied
genuinely observed original-source bytes. Quotes are UNTRUSTED, must be
HTML escaped, and never executed or placed into system prompts. Only
synthetic/mock content can show two-positive cases in this scope.
The real two-host canary deliberately demonstrates a justified refusal,
NOT two real publisher statements corroborating a fact.

External HTTPS deployment (older Step234) remains deferred at user request.
Open GitHub release issue #242 is not Step242 engineering. No LLM-generated
answers, automatic actions, arbitrary web source discovery, general NLI
accuracy improvement or production deployment in Step244.

## Acceptance evidence requirements

The engineering milestone remains PROVISIONAL until PR merge and all
EIGHTEEN GitHub Actions PUSH workflows on the exact FINAL main SHA
finish success. Independently inspect the complete backend test log,
focused Step244 suite log and genuine HTTPS client canary. A successful
PR-head build alone does not meet this condition. Any follow-up
documentation acceptance merge creates a new main SHA, which requires
its own exact-SHA workflow verification. Record the final acceptance
evidence in the PR audit rather than introducing another untested commit.

## Application usage example

An operator must first configure the pilot bearer and exact two-origin
source allowlist. A developer imports TwoOriginAnswerRequest from
backend.app.api.two_origin_answer and check_two_origin_answer_with_api
from backend.app.integrations.two_origin_answer_client, constructs
a validated request with one claim, entity, two allowed HTTPS URLs and
freshness, and calls:

    answer = check_two_origin_answer_with_api(trusted_client, bearer, request)

The trusted_client is deliberately injected and must be configured to
authenticate the intended backend server. If answer.decision is
source_disagreement, never convert it to verified factual truth. If
answer.decision is abstain, answer.citations is empty; do not fabricate
partial source evidence. Quotes are untrusted data for escaped display.

## Independently verified implementation merge acceptance (15 October 2026)

- [PR #270](https://github.com/riteshchavan96k/ai-reality-layer/pull/270)
  merged into actual main `bf5cee59b285bb23c9ada32d02d8868e9d008dd7`.
  All **18 GitHub Actions push-event workflows completed success on exactly this
  merged main SHA**. PR-head checks alone were not used as completion evidence.
- [Full backend run 38628208979](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38628208979):
  **2,910 tests passed**, including prior 2,840 and 70 Step244 adversarial
  client integration tests (quote tampering, request swaps, credentials,
  independent bounded relationship rechecks and incomplete source refusal).
- [Dedicated Step244 run 38628208978](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38628208978):
  **70 passing cases**, plus real Python.org and IANA HTTPS into the
  authenticated local FastAPI two-origin API and downstream fail-closed
  application adapter. Both source orders correctly abstained with **zero
  citations**, and off-list and unauthorized requests made no source fetch.
- Real publisher positive corroboration has NOT occurred. Two-positive,
  two-negative and mixed outcome contract tests used synthetic/mocked original
  source bodies; no real-world truth, independent ownership, signed
  publisher attestation or external deployment is asserted.
- Scoped Step244 engineering implementation has passed the 18/18 exact
  main SHA gate. This documentation acceptance synchronization is itself a
  new Git commit and requires **another 18/18 exact-final-main check**
  before final acceptance; record that in PR #271's comments without
  altering that final checked code revision.
