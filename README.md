## Step 250: On-demand live original-source reconciliation against historical Reality State

AI Reality Layer now exposes `POST /api/v1/reality-state/timeline/recheck`
for one operator-approved claim/timeline and exactly **one** fresh HTTPS
original-source observation. Pilot bearer authorization, exact source URL
allowlist and **`ARL_TEMPORAL_RECHECK_API_ENABLED=1`** are required. Historical
timeline validation runs in private SQLite read-only mode **before** the
network request; the existing source-cited answer pipeline is called in-process
once (no nested self-HTTP); the shared Step246 comparison classifies the
change. The entire history is checked again afterward to reject a concurrent
append or corruption. No history write occurs.

The response includes the baseline root/latest ID, old/new timestamped capture
and quote SHA-256 hashes, bounded source decisions and conservative change
classification, or a **no-partial-receipt abstention**. Publisher quotes,
secrets and database paths are omitted. Applications can use
`check_temporal_reconciliation_with_api(client,token,request,root_id)` with
a trusted transport and strict fail-closed response validation. Historical
evidence never becomes current evidence; a fresh aligned source statement is
only **bounded source evidence**, not objective factual truth. No scheduler,
autonomous agent, new model, deployment or official historical attestation is
claimed. External deployment gate #242 remains separate.
[Scope and operator example](docs/STEP_250.md).

## Step 249: Read-only authenticated historical Reality State API for applications

A new `POST /api/v1/reality-state/timeline` endpoint exposes **validated
historical source-observation metadata** to authorized AI applications without
fetching publishers or modifying SQLite. The server must explicitly set
`ARL_TEMPORAL_HISTORY_API_ENABLED=1`, alongside `ARL_RUNTIME_MODE=pilot`,
the existing pilot bearer token, exact HTTPS source URL allowlist, and the
private local Step247/248 history store and operator HMAC key. When not opted
in, historical access abstains; incorrect bearer authorization remains denied.

Input contains one `root_record_id` (the Step247 baseline record ID) and the
exact canonical `OriginalSourceClaimRequest`. Output is a maximum 64-entry
bounded history with decisions, UTC timestamps, capture hashes and validated
change classifications but **no raw source quotations or HMAC secrets**.
The store is checked using SQLite `mode=ro` and source URLs are never
dereferenced by this route. Invalid/tampered/unavailable history abstains.

Application code can call
`check_temporal_timeline_with_api(client,token,request,root_record_id)`
using an authorized trusted-transport client. The strict result parser
rejects structurally altered responses, false-like epistemic flags, mismatched
claims, misleading chronology and contradictory hash-based change labels.
**Even a valid historical source reading is not current evidence** and cannot
establish publisher ownership, independent historical timestamps or factual
truth. No external hosting or background monitoring is introduced.
[Step249 scope, usage and acceptance](docs/STEP_249.md).

## Step 248: Longitudinal Reality State evidence timeline

The original-source observation history now supports an operator-controlled
**sequence** of bounded source checks over time. After Step247
`--live --save-observation` returns a `saved_record_id`, use that ID as the
timeline root for subsequent explicit `--live --timeline-append ROOT_ID`
operations with the **same claim, entity, original HTTPS source and freshness
window**. Each successful comparison saves the latest verified source reading
atomically with an integrity-checked link; a future append compares against
the current final entry, not the original baseline. A new
`--timeline-show ROOT_ID` command validates the complete history and returns
bounded hashes, source timestamps and per-step classification **without HTTPS**
or raw source quotations. It does not require `--live` but retains existing
operator pilot, source allowlist and private-store authorization.

The timeline is limited to 64 observations, with at most 1,000 observations
across the private database. HMAC protects operator-held records and links;
neither historical authenticity nor rollback resistance nor publisher
authorship can be inferred. Unavailable evidence does not create a new
history entry. There is **no automatic polling** or external deployment.
See [Step 248 scope and safety gates](docs/STEP_248.md).

## Step 247: Durable local original-source evidence history across operator sessions

AI Reality Layer now offers opt-in **persistent, keyed original-source observations**.
One command records a verified single-source observation; a **later, separate
CLI process** can reopen that operator-MACed baseline and make exactly one fresh
authenticated HTTPS observation of the *same narrow claim and approved URL*.
No background monitoring, arbitrary web search, publisher-signed chronology,
factual truth guarantee or externally hosted deployment is implied.

Before using the commands below, securely provision a directory accessible only
to the operator (0700), and supply a **persistent 32-byte random secret encoded
as 64 hexadecimal characters** from an operator-managed secret store. Never
copy a secret into terminal commands, Git history, issue bodies or logs.
`ARL_OBSERVATION_STORE_PATH` must be an absolute, normalized `.sqlite3`
path directly inside that private directory, with no symlinks. File permissions
are checked at every access. The operator must already configure the existing
`ARL_RUNTIME_MODE=pilot`, `ARL_PILOT_BEARER_TOKEN` and exact
`ARL_INDEPENDENT_SOURCE_ALLOWED_URLS` allowlist.

```sh
# Configure ARL_OBSERVATION_STORE_PATH and ARL_OBSERVATION_HMAC_KEY_HEX
# securely in the operator environment before executing either command.
python -m backend.app.cli --live --save-observation \
  --claim "Python 3.13.0 is a stable release." \
  --entity "Python 3.13.0" \
  --source "https://www.python.org/downloads/release/python-3130/"
# Retain only the safe, random saved_record_id from that JSON.
python -m backend.app.cli --live --recheck-record <saved_record_id> \
  --claim "Python 3.13.0 is a stable release." \
  --entity "Python 3.13.0" \
  --source "https://www.python.org/downloads/release/python-3130/"
```

The claim, entity, URL **and exact freshness window** must match the saved
request. A changed key invalidates prior records; preserve it in secret
management if later rechecks are needed. Source quotes are stored as **untrusted
local data**, not printed by default; secure backups, retention and safe disposal
are the operator's responsibility. At most 1,000 records are accepted;
no automatic pruning/rollback-resistant ledger is claimed. HMAC only provides
operator-controlled integrity, not reliable capture chronology, operator
non-repudiation or publisher signatures. A stale baseline is valid **only for
comparison**, never current evidence.

See [Step 247 scope, security and reproducibility](docs/STEP_247.md).
The separate Step234 external hosting release gate remains pending.

# ai-reality-layer
## Step 246: Opt-in original-source temporal recheck (single approved HTTPS page)

A local operator can now explicitly compare **two separate original-source
HTTPS observations** of the *same narrow claim* on the *same one
operator-allowlisted URL* without writing Python. Uses existing authenticated
local pilot, Step241 original-source answer and Step242 application consumer
with new `backend.app.integrations.source_recheck` consistency checks.
Only complete rechecks expose both capture hashes/quote hashes and UTC
observation metadata. The result can be unchanged raw source capture, changed
raw capture with unchanged bounded statement, changed bounded statement,
or strict no-receipt abstention. The SDK also lets a trusted application
retain a previously validated in-memory answer and re-check it later.
There is **NO signed historical attestation, event store, scheduler, automatic
monitoring, objective-truth guarantee or new publicly exposed service**.

```sh
python -m backend.app.cli --live --recheck \
  --claim "Python 3.13.0 is a stable release." \
  --entity "Python 3.13.0" \
  --source "https://www.python.org/downloads/release/python-3130/"
```

As in Step245, configure operator pilot bearer and exact source URL
allowlist securely, and never put credentials in argv. Untrusted original
source quote bodies are omitted unless explicitly opted into; any UI must
escape them. See [Step246 technical contract](docs/STEP_246.md).
## Step 245: Real local operator claim check with original-source citations

An AI developer can now perform an **actual bounded claim check** without
writing new Python integration code. The opt-in `python -m backend.app.cli`
uses the already authenticated and validated single-source or two-source
clients inside the existing local pilot; it does not expose a public server
or silently fetch arbitrary URLs. Specify a claim, entity and one or two
exact operator-approved HTTPS `--source` URLs and **explicit `--live`**.
The bearer token is read only from `ARL_PILOT_BEARER_TOKEN`; pilot mode and
`ARL_INDEPENDENT_SOURCE_ALLOWED_URLS` must already be set by the operator.
Never put credentials in command-line arguments or source code.

```sh
python -m backend.app.cli --live \
  --claim "Python 3.13.0 is a stable release." \
  --entity "Python 3.13.0" \
  --source "https://www.python.org/downloads/release/python-3130/"
```

Output is **machine-readable bounded source observation**, including a quote
hash/source URL/timestamp only after verification. Raw source quotes are
excluded by default; `--include-untrusted-quotes` is an explicit choice,
and quote text must be escaped before user-interface rendering.
The operator CLI uses existing fixed response templates and cannot assert
factual truth, publisher-authenticated authorship, or general semantic QA.
A second unrelated IANA source correctly produces abstention, not
fabricated corroboration. See [Step245 usage, safety and tests](docs/STEP_245.md).

## Step 244: Defensive application consumer for two original-source citations

An AI application can call `check_two_origin_answer_with_api(client, token, request)`
from `backend.app.integrations.two_origin_answer_client`. It makes **one**
authenticated Step243 compare API request; verifies pair request identity
including both URL ordering, static bounded outcome, false epistemic fields,
each original quotation/hash/capture timestamp and the conservative
claim-to-quote grammar relationships; and exposes an **immutable two-citation
tuple** only if the entire pair verifies. Tampered or partial results abstain
without either quote, URL, or capture receipt. A verified source disagreement
**cannot authorize an AI to assert support**. The API transport must be
trusted and authenticated; a SHA256 is not a publisher signature, and two
different hostnames do not establish independent ownership or real-world truth.

```bash
python -m pytest -q backend/tests/test_step244.py
python -m backend.app.evaluation.step244_live_two_origin_client --live
```

The opt-in live canary tests real Python.org/IANA HTTPS and **correctly
abstains** for the unrelated second site. Positive and disagreement tests
use MOCKED source text, not real independent confirmation. No public hosting.
[Step244 scope and acceptance](docs/STEP_244.md).

## Step 243: Two separately observed HTTPS hosts, one bounded claim

The authenticated `POST /api/v1/reality-state/answer/compare` can now
compare one explicit narrow claim against **exactly two operator-allowlisted
HTTPS URLs on different hosts**. Each original-source observation and citation
must pass the same source assurance and tamper/freshness checks as the existing
single-source Step241/242 answer route. Two alignments produce two individually
bound citations; two contradictions produce a bounded contradiction; mixed
source statements surface `source_disagreement` **without** a support upgrade.
If either source fails, the pair abstains and exposes **no partial citations**.
It cannot discover new URLs, assert factual truth or prove independent
publishers. The test suite uses simulated positive and disagreement source
content; actual Python.org + IANA HTTPS canary proves failure-safe abstention,
not real publisher corroboration.

```bash
python -m pytest -q backend/tests/test_step243.py
python -m backend.app.evaluation.step243_live_two_origin --live
```

The second command deliberately accesses fixed real HTTPS sites, and must be
opted into explicitly. See [Step243 technical scope](docs/STEP_243.md).
External hosting remains deferred.

AI Reality Layer — infrastructure for giving autonomous AI systems continuously verified information about the world before they reason, decide, or act.

## Step 241: First bounded original-source answer with exact citation

Authenticated clients can use `POST /api/v1/reality-state/answer` with **the exact same validated claim/source/entity/freshness request** as the claim API. This is the first *directly usable, source-cited AI application answer*: a fixed, transparent statement describing only the **bounded relationship between the claim and one server-observed original-source statement**, plus the exact excerpt, approved publisher URL, excerpt SHA-256, original HTTP capture SHA-256 and UTC observation time as data-only citation fields.

The new endpoint calls the current independently source-assured claim pipeline **exactly once**. It emits a citation only when that result passes the entire previous Step235 request-bound source guard, matches the same capture/quote digest, and is `bounded_supported` or `bounded_contradicted`. On unsupported grammar, quotation, conflict, stale/unapproved/unavailable evidence or invalid authentication, it returns **an explicit abstention without a citation or quote** (or rejects unauthorized access). No LLM can invent answer details: the answer template is fixed and never interpolates untrusted source content. The quote field is untrusted source data and **must be HTML-escaped by any rendering UI**. Neither source-text agreement nor source-cited answer means independently certified factual truth.

```bash
# normal Python backend, no ML dependencies
python -m pytest -q backend/tests/test_step241.py
# explicit genuine Python.org HTTPS authenticated integration test
python -m backend.app.evaluation.step241_live_cited_answer --live
```

Step240 developer NLI veto integration stays separate and unchanged; no model can promote source evidence and no public hosting is done. [Step241 technical scope](docs/STEP_241.md).

## Step 240: Bound original-source excerpt handoff and optional fail-closed NLI veto

A real AI client can now obtain the **exact bounded original-source statement actually selected by the authenticated claim-only API**, plus text SHA-256 and the **same** server capture SHA-256/UTC time, only after all strict independent-source/quotation/counterstatement gates pass. The already trusted Step235 client gate remains unchanged. Optional Python client `check_claim_with_semantic_veto(client, token, request, model=reviewed_model)` does **one authenticated request** and compares the verified source statement as neural *premise* against the requested claim as *hypothesis*.

An NLI `entailment` can **only retain the underlying already-bounded-supported** decision; NLI neutral/contradiction/missing/untrusted/failed model **abstains**. A source contradiction stays contradicted without running NLI, and any source abstention can never become supported. No model download in the API or production Docker; consumers initialize/inject a separately reviewed neural model explicitly.

```bash
# Deliberate opt-in for genuine local FastAPI + Python.org TLS + pinned ONNX NLI
python -m pip install -r backend/requirements-nli-shadow.txt
python -m backend.app.evaluation.step240_live_semantic_veto --live
```

Output is bounded/traceable original-source **evidence**, not publisher-signed factual truth. The SNLI benchmark observed **3 false entailments among 80 non-entailment pairs** on a small convenience sample; it cannot establish this added gate improves real-world accuracy. This is a conservative optional risk veto, NOT unrestricted semantic validation or automatic model-based claim promotion. [Step240 specification](docs/STEP_240.md).

## Step 239: First external human-annotated neural NLI error-rate evaluation

This optional standalone experiment tests our **actual pretrained ONNX NLI model** against a SHA-256-checked human-annotated Stanford SNLI `validation` file. It uses a strictly fixed first-40-eligible-per-class sample (120 total), verifies labels were **external crowdsourced SNLI annotations rather than AI-generated by us**, and reports confusion matrix, per-class precision/recall, and especially **false entailment on human-neutral / human-contradiction examples**. No raw corpus text, private data, or model secrets are logged.

```bash
python -m pip install -r backend/requirements-nli-quality.txt
python -m backend.app.evaluation.step239_external_nli_quality --live
```

The dataset is Stanford SNLI ([dataset card](https://huggingface.co/datasets/stanfordnlp/snli), CC BY-SA 4.0; Bowman et al. 2015). The corpus is mostly caption-derived general-language semantics; our model has SNLI-family training. The **nonrandom, convenience-selected 120 examples are not representative** and do not measure real-world truth, original-source accuracy, or out-of-domain production safety. This evaluation does NOT authorize neural claim support, change the Reality State API, or enable public deployment. [Step239 technical scope](docs/STEP_239.md).

## Step 238: Real original-source HTTPS -> genuine neural NLI (shadow only)

The first **live original-publisher** neural experiment now takes its NLI *premise* from **one** actual TLS-validated and operator-allowlisted Python.org capture, rather than developer-supplied text. It validates the capture receipt and UTC freshness, selects exactly one matching complete unquoted source unit and compares three fixed developer-written claims with the **real pinned** Step237 ONNX Transformer. No source text is printed to the audit, and the model cannot authorize Reality State support.

```bash
# Explicitly opt in to model download and one public HTTPS source observation:
python -m pip install -r backend/requirements-nli-shadow.txt
python -m backend.app.evaluation.step238_live_source_nli --live
```

Not a general source-discovery or model-verification API. Claims are developer-authored, lack independent human gold, and should not be scored as field factual accuracy. Failure to retrieve a fresh unique source unit abstains; there is no fallback to a forged or user-supplied excerpt. No public deployment. [Step238 scope and limitations](docs/STEP_238.md).

## Step 237: Actual pretrained neural NLI in isolated shadow mode

A first **real Transformer** entailment/contradiction/neutral model can now run via optional ONNX Runtime CPU inference on the frozen Step236 candidate corpus. Its real model predictions are recorded **alongside** the deterministic parser baseline. The operator must explicitly opt in to one pinned Hugging Face model download; no NLI model is added to the normal API or Docker image and no prediction may authorize source support.

```bash
# Only to deliberately run the optional ML experiment, not needed for normal backend work:
python -m pip install -r backend/requirements-nli-shadow.txt
python -m backend.app.evaluation.step237_nli_shadow --live --summary-only
```

The reviewed pretrained weights (`cross-encoder/nli-MiniLM2-L6-H768`, Apache-2.0) are downloaded from a fixed model revision and checked against a public ONNX SHA-256. Only the 20 frozen **developer-authored, not independently reviewed** cases are scored: these are **not factual-truth labels**. Neural softmax scores are uncalibrated and can be wrong. No source-content observation or production Reality State decision changes in Step237. See [Step 237 scope](docs/STEP_237.md).

## Step 236: Frozen semantic verification baseline and blind reviewer handoff

This benchmark makes our **actual deterministic parser limitation measurable** before introducing a genuine neural NLI model. It uses twenty short **developer-authored, not independently human-labeled** candidate pairs, including deliberately forged excerpts associated with genuine source URLs and eight explicitly fictional semantic scenarios.

```bash
python -m backend.app.evaluation.step236_semantic_baseline --summary-only
python -m backend.app.evaluation.step236_semantic_baseline --summary-only --blind-packet /tmp/arl-blind-review.json
# ONLY after two real external reviewers submit complete labels:
python -m backend.app.evaluation.step236_semantic_baseline --summary-only --review-file /path/to/reviewer-labels.json
```

The blind packet **does not include** baseline predictions, earlier developer labels or a truth key. Conditional scoring refuses incomplete/disputed reviewer pairs; it always reports reviewer identity and independence as **not externally authenticated**. It never claims population factual accuracy, real publisher certification, or a tested NLI model. Real independent reviews, diverse authorized source capture and future Transformer evaluation are separate needed actions. [Scope and limitations](docs/STEP_236.md).

## Step 235: Safe AI application consumer for bounded Reality States

An application can now call the authenticated claim-only endpoint through an **explicit API transport** and receive a small fail-closed decision instead of trusting a free-form `status` string.

```python
from fastapi.testclient import TestClient  # local integration example, not external hosting
from backend.app.main import app
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.ai_claim_gate import check_claim_with_api

request = OriginalSourceClaimRequest(
    entity="Python 3.13.0",
    claim_text="Python 3.13.0 is a stable release.",
    source_uri="https://www.python.org/downloads/release/python-3130/",
)
with TestClient(app) as client:
    decision = check_claim_with_api(client, pilot_token_from_operator_secret_manager, request)
    if decision.may_use_as_bounded_evidence:
        # Pass only this bounded evidence indicator to the calling AI system.
        pass
    else:
        # The AI system must abstain or seek human review, not invent certainty.
        pass
```

This example assumes the **operator already configured** pilot mode, approved original-source URL, and a valid token. The `pilot_token_from_operator_secret_manager` identifier is a user-provided variable, not a built-in value. No external deployment is necessary to test the local integration. The adapter never chooses a network destination: the calling application owns its authenticated API transport, TLS verification and secrets. Its decisions are `bounded_supported`, `bounded_contradicted`, and `abstain`; only the first permits using a **narrowly source-aligned evidence indication**, not factual truth or unrestricted agent action. The SHA-256 request binding prevents accidental wrong-request reuse **only when the API transport itself is trusted**; it is not cryptographic publisher authentication. See [Step 235's scope and acceptance limits](docs/STEP_235.md).

## Core original-source claim-only verification (bounded MVP)

An AI client can now submit one explicit claim and an operator-approved original HTTPS source **without providing a potentially forged source excerpt**:

```http
POST /api/v1/reality-state/claim
Authorization: Bearer <operator-managed-pilot-token>
Content-Type: application/json

{
  "entity": "Python 3.13.0",
  "claim_text": "Python 3.13.0 is a stable release.",
  "source_uri": "https://www.python.org/downloads/release/python-3130/",
  "freshness_max_age_seconds": 3600
}
```

The operator must configure the exact original-source URL in `ARL_INDEPENDENT_SOURCE_ALLOWED_URLS`. The backend independently retrieves the source over strictly validated HTTPS, selects **one unambiguous complete atomic source assertion**, and reuses the *same observation* for the existing strict independent text-match, source quotation/counterstatement, freshness and claim-alignment Reality State pipeline. If the statement is missing, duplicated, conflicting, quoted or outside the supported grammar, it **abstains rather than manufacturing support**. The JSON response contains a bounded `status` and `reason`, with `reality_state` when a unique candidate is evaluated.

This is **not unrestricted web search, a semantic fact checker, publisher authentication or independently verified factual truth**. The claimant still names a candidate exact operator-allowlisted source; the system does not discover an official publisher on its own. The fixed Python.org real-original-source CI canary verifies a bounded positive and its safely refused negation; it does not establish population accuracy or external hosting. See [core implementation and limitations](docs/CORE_ORIGINAL_SOURCE_CLAIM.md). External HTTPS deployment remains **deferred and explicitly blocked for real users** by [#242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242).


## Authenticated restricted single-tenant pilot engineering (Step 231)

The original-source FastAPI backend has a **development-only default mode**. Never expose default development mode on a public interface. The explicitly configured Step 231 pilot adds a server-owned bearer authorization boundary, strict configured exact original-source URL allowlist, a 4 MiB application request limit and a reproducible non-root Docker image. The explicitly revised **Step 231 engineering milestone is complete**: [PR #241](https://github.com/riteshchavan96k/ai-reality-layer/pull/241) plus [CI stability fix #243](https://github.com/riteshchavan96k/ai-reality-layer/pull/243), with **2,440 backend tests and five successful workflows on exact merged implementation `main` `9e21809cc69fdac1ca998f11b58b1cdf862ed3d0`**. Those checks include real loopback Docker HTTP and genuine Python.org DNS/TLS/HTTPS original-source observation. This is a verified deployable implementation, **not an externally hosted service**. See [engineering scorecard](docs/STEP_231_ENGINEERING_SCORECARD.md).

**External HTTPS hosting and independent outside-client testing remain a mandatory separate release gate, [#242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242)**. TLS ingress, external identity/secret rotation, rate limits, operational controls and source-accuracy evaluation are not certified by the Docker smoke test. The 2026-10-13 scope decision explicitly separated the engineering milestone from real external hosting to prioritize core AI Reality Layer functionality; do not claim public deployment or production readiness until that issue's controls pass. See [docs/STEP_231.md](docs/STEP_231.md) for the revised acceptance criteria and safe local runtime.

## Development validation

Install the production and test dependencies through the development requirements file, then run the complete backend regression suite from the repository root:

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest
```

GitHub Actions runs the same backend test suite automatically on pushes and pull requests to `main`.

## MVP current-information retrieval

AI Reality Layer can use an opt-in provider-neutral HTTPS retrieval endpoint for current/external evidence.

Configure an endpoint template containing the literal `{query}` placeholder:

```bash
export ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE='https://retrieval.example.com/search?q={query}'
```

The endpoint must use HTTPS. A successful response should be a JSON object such as:

```json
{
  "status": "completed",
  "content": "Company X launched Feature A today.",
  "sources": [
    {
      "title": "Official Company X update",
      "uri": "https://example.com/company-x"
    }
  ]
}
```

Then call:

```http
POST /api/v1/reality-state
Content-Type: application/json

{
  "task": "What is the current status of Company X?"
}
```

The retrieval service supplies source content only. AI Reality Layer performs the deterministic claims, evidence-linking, provenance, observation, freshness, conflict, confidence-signal, and Reality State assembly stages.

If no retrieval endpoint is configured, requests that require external/current evidence fail closed through the existing unavailable/insufficient Reality State path rather than fabricating evidence.

## Already have search or RAG evidence?

Use the direct evidence endpoint instead of configuring AI Reality Layer retrieval:

```http
POST /api/v1/reality-state/evidence
Content-Type: application/json

{
  "task": "What is the current status of Company X?",
  "documents": [
    {
      "title": "Company X official update",
      "uri": "https://example.com/company-x-official",
      "content": "Company X launched Feature A today."
    },
    {
      "title": "Independent report",
      "uri": "https://example.com/company-x-report",
      "content": "not Company X continues to operate."
    }
  ]
}
```

The documents remain source-scoped during claim extraction, so claims retain the URI(s) they actually came from. Exact duplicate claims across sources are merged while preserving all source references.

This endpoint does not fetch the submitted URIs and does not run the configured retrieval provider. It processes the supplied evidence through evidence-quality validation, claim extraction, claim/evidence linking, provenance, observation, freshness, conflict detection, confidence signals, and Reality State assembly.

Freshness remains uncertain in this initial direct-evidence contract because ingestion time is not treated as source publication time.

## Optional freshness policy for supplied evidence

If your search/RAG/connector already knows when each source was observed, include `observed_at` on every document and declare a freshness window:

```http
POST /api/v1/reality-state/evidence
Content-Type: application/json

{
  "task": "What is the current status of Company X?",
  "freshness_max_age_seconds": 3600,
  "documents": [
    {
      "title": "Company X official update",
      "uri": "https://example.com/company-x",
      "content": "Company X launched Feature A.",
      "observed_at": "2026-10-03T12:30:00Z"
    }
  ]
}
```

`observed_at` means when your system observed the source, not when it was published or independently verified. It must be a timezone-aware ISO-8601 timestamp and cannot be in the future.

When a freshness window is declared, every document must include `observed_at`. Sources inside the declared age window are assessed as fresh; older sources are stale. If no freshness window is supplied, freshness remains unknown even when observation timestamps are present.

If no `observed_at` is supplied, AI Reality Layer records the submission ingestion time for observation metadata but does not use that ingestion time to claim the evidence is fresh.


## Scoped retrieval provenance (Step 182)

For **more than one retrieved source**, the configured HTTPS retrieval service must supply
the text belonging to each original source. A combined text body plus several source
URLs does **not** establish which source supports a claim.

Example of the supported provider-neutral response:

```json
{
  "status": "completed",
  "sources": [
    {
      "uri": "https://example.com/original-a",
      "title": "Original A",
      "content": "Company X launched Feature A. Shared fact."
    },
    {
      "uri": "https://example.com/original-b",
      "title": "Original B",
      "content": "Company X expanded its team. Shared fact."
    }
  ]
}
```

The optional top-level `content` must equal the source documents joined with a
blank line (after trimming each document), if it is supplied. Otherwise the
Reality Layer constructs that combined content itself.

Unique claims are linked only to their contributing original URI, and exactly
duplicate claims merge source references. Multi-source legacy responses without
source-level text do **not** produce misleading claim citations: extraction
becomes unavailable due to ambiguous source attribution. Single-source legacy
responses remain valid.

The retrieval endpoint's own URL is never substituted as the original
publisher's URI if no source is returned. A URI is **caller/provider-supplied
provenance**, not independent verification or proof of factual truth.

See `docs/STEP_182.md` for the full boundary and regression contract.

## Optional freshness policy for configured retrieval (Step 183)

The configured HTTPS retrieval path now supports **provider-reported source
observation times**, separate from the time the Reality Layer processes the
provider response. To declare a freshness requirement, use:

```http
POST /api/v1/reality-state
Content-Type: application/json

{
  "task": "What is the current status of Company X?",
  "freshness_max_age_seconds": 3600
}
```

A source-scoped retrieval response may supply:

```json
{
  "status": "completed",
  "sources": [
    {
      "uri": "https://example.com/original-a",
      "content": "Feature A launched.",
      "observed_at": "2026-01-01T12:30:00Z"
    },
    {
      "uri": "https://example.com/original-b",
      "content": "Feature B launched.",
      "observed_at": "2026-01-01T18:15:00+05:30"
    }
  ]
}
```

`observed_at` means **when the retrieval provider says it observed that
original source**, **not** when the publisher posted it, when the event
occurred, or when AI Reality Layer verified the source. These are
provider-reported times, not independently authenticated statements. All
source timestamps require explicit timezones and cannot be in the future.

When a freshness window is requested, **every source must have a provider-
reported observation timestamp**. Missing timestamps make freshness
unavailable and prevent supported confidence; using the current processing
time as a substitute would misleadingly classify cached evidence as fresh.
Stale sources force uncertainty. Without a declared window, freshness
remains unknown even if observations exist. Legacy single-source and
task-only retrieval requests still work.

See `docs/STEP_183.md` for full rules, compatibility and regression scope.

## Bounded configured retrieval (Step 184)

The configured HTTPS retrieval path now rejects oversized or unexpected
source data **before** extracting claims. These boundaries match the
existing direct-evidence MVP document limits wherever applicable:

- Maximum **20** sources per response.
- Maximum **50,000 characters** of content per original source.
- Maximum **2,048** URI characters and **500** title characters.
- Maximum **64** characters for an optional provider `observed_at` value.
- Maximum **2,000 unique candidate claims** extracted from a retrieved
  response. Inputs exceeding the claim budget produce no partial claims.

The canonical `sources[]` fields are `uri`, `title`, `content`, and
`observed_at`. Small legacy scalar fields such as `id` or `url` remain
compatible but are discarded during evidence normalization; oversized or
nested extras are rejected instead of entering the Reality State. Combined text has a bounded
length matching the number of original sources; Step 182's exact aggregate
consistency validation still applies. The HTTPS adapter's existing byte
limit remains in effect.

For invalid retrieved evidence, the system fails closed with a structured
unavailable/insufficient Reality State rather than partially attributing
claims or labeling unsupported evidence as verified. The direct-submitted
evidence API is unchanged.

See `docs/STEP_184.md` for the precise limits and compatibility tests.

## Submitted-evidence claim budget (Step 185)

The existing developer-supplied evidence endpoint
`POST /api/v1/reality-state/evidence` now limits **each entire
submission** to **2,000 distinct deterministic candidate claims**, across
all documents. The existing maximum of 20 documents and 50,000 characters
per document still applies.

Identical claims repeated in multiple original documents are merged and
retain every contributing original source URI without consuming additional
unique claim slots. On an over-budget submission, the pipeline fails
conservatively with `submitted_claim_limit_exceeded` and emits **no partial
claims, citations/claim links, or supported confidence**. In the underlying
Python bundle API, lazy document iterables are also read only up to the
first over-limit (21st) item, avoiding unbounded materialization.

The retrieval-based API's independent Step 184 budget, Step 181–183
freshness and provenance rules, and the generic lower-level `usable`
claim extractor contract remain unchanged.

See `docs/STEP_185.md` for examples, reasons, safety boundaries and
regression coverage.

## Finite freshness policies (Step 186)

Both `POST /api/v1/reality-state` (configured retrieval) and
`POST /api/v1/reality-state/evidence` (developer-submitted evidence)
support an optional `freshness_max_age_seconds`.

The policy must be a **positive, finite JSON number**, not a boolean,
numeric string, zero, negative value, NaN, infinity or unrepresentably
large integer. The same rule applies to the underlying Python
retrieval/domain contracts and the freshness evaluator; canonical source
freshness assessments also reject nonfinite age/window measurements.
This prevents a positive infinite window from classifying arbitrarily
old observations as fresh or allowing a non-JSON NaN result.

If the policy is **omitted**, observation-age freshness remains unknown.
Finite windows classify only **source observation age**, never the
publication date, authenticity or factual truth of a source. Existing
source-scoped provenance and evidence limits remain in place.

See `docs/STEP_186.md` for contract details and full regression scope.

## Auditable submitted evidence (Step 187)

The direct developer-evidence endpoint
`POST /api/v1/reality-state/evidence` now includes **the trimmed original
`content` for each original source** in its canonical
`response.evidence.sources[]` entries, alongside `uri` and `title`.
Its top-level `response.evidence.content` remains the deterministic
two-newline concatenation of those original per-source texts.

This makes the returned evidence independently auditable: for
**in-budget** submitted requests, the existing
`EvidenceClaimExtractor().extract_result(response["evidence"])`
reconstructs the same candidate claims and original source URI
attribution as `response["claims"]`, including duplicate claims
reported by multiple sources.

The `source_observation` object remains the authoritative structured
place to distinguish caller-reported `observed_at` from ingestion
timestamps. Observations do **not** certify publication time, origin
ownership, or factual truth. The returned text is still developer-
supplied, untrusted evidence rather than independently verified content.

The explicit per-source content also duplicates text already present
in the aggregate field: consumers must account for the increased
response size (requests are already limited to 20 × 50,000-character
documents). The existing 2,000-unique-claim cap and no-partial-claim
failure behavior are unchanged.

See `docs/STEP_187.md` for contract details and end-to-end tests.

## Shared observation timestamp bounds (Step 188)

The optional source `observed_at` values used by both the configured
retrieval path and `POST /api/v1/reality-state/evidence` now share the same
**64-character maximum**, applied to the **raw string** before timestamp
normalization. The limit is enforced by the HTTP/API request model and by
Python/domain and canonical source-observation validation so direct callers
cannot bypass the API constraint. Values exceeding 64 characters are
rejected; 64-character or shorter nonblank, timezone-aware ISO-8601 values
are validated and normalized to UTC `Z` as before.

For example, `2026-01-01T18:00:00+05:30` normalizes to
`2026-01-01T12:30:00Z`. Future times, timezone-naive, invalid and blank
values are still rejected. A missing timestamp remains valid **only when no
explicit freshness window requires that source observation**, and
does not create an assertion of fresh source evidence.

This metadata is an observation **reported** by the caller or provider,
not an independently verified publication time or proof of factual truth.
Existing source URI lineage and claim/evidence limits are unchanged.
See `docs/STEP_188.md` for API details and regression tests.


## Canonical observation/freshness timestamps (Step 189)

Canonical internal source-observation and source-freshness records now enforce
the same `observed_at` contract as the Step 188 public/provider boundaries.
Direct typed construction and mapping deserialization reject oversized,
malformed, timezone-naive, blank, non-string, and future timestamps, and
normalize valid timezone offsets to UTC `Z`.

This means equivalent values such as
`2026-01-01T18:00:00+05:30` are serialized canonically as
`2026-01-01T12:30:00Z` in both `source_observation` and `freshness`
records. Existing fresh/stale/unknown policy semantics, finite age/window
checks, source lineage, and claim/conflict/confidence behavior are unchanged.

`observed_at` remains source-observation metadata only. It is not a verified
publication timestamp, source-authenticity assertion, or factual-truth proof.

See `docs/STEP_189.md` for the invariant and regression scope.


## Canonical freshness classification integrity (Step 190)

Canonical `SourceFreshnessAssessment` records now require their declared
classification to agree with their own finite age/window measurements:

- `fresh` requires `age_seconds <= max_age_seconds`
- `stale` requires `age_seconds > max_age_seconds`

The exact boundary remains fresh, matching the existing evaluator. This rule
also applies when `SourceFreshnessResult` is reconstructed from mappings, so a
deserialized canonical result cannot claim `fresh` or `stale` while carrying
contradictory measurements.

Step 186 finite-number protections and Step 189 canonical `observed_at`
validation remain unchanged. Unknown freshness remains reason-based, and this
step does not change confidence aggregation, publication-time semantics, source
authenticity, or factual-truth claims.

See `docs/STEP_190.md` for the exact invariant and regression scope.


## Unknown freshness policy integrity (Step 191)

Canonical `SourceFreshnessAssessment` records now reject `status="unknown"`
when `max_age_seconds` is present. In the current MVP contract, unknown
freshness means that no explicit freshness policy window was declared; once a
window exists, a usable observation must be classified as fresh or stale under
the Step-190 inequality.

This rule also applies to `SourceFreshnessResult` mapping/deserialization
paths. A finite `age_seconds` may still be retained without a policy window,
because observation age can be measurable even when the system correctly
refuses to classify freshness.

Existing Step-186 finite-number checks, Step-189 timestamp canonicalization,
Step-190 fresh/stale consistency, and conservative confidence behavior remain
unchanged.

See `docs/STEP_191.md` for the exact invariant and regression scope.


## Canonical freshness count type integrity (Step 192)

Canonical `SourceFreshnessResult` count fields now require strict
non-negative integers. `source_count`, `fresh_count`, `stale_count`, and
`unknown_count` reject booleans, floats, strings, and negative values before
count/state consistency is checked.

This closes Python equality loopholes such as `True == 1`,
`False == 0`, and `1.0 == 1`, which could previously allow non-integer
count representations through mapping/deserialization paths.

Normal evaluator and helper outputs already use real integer counts, so
fresh/stale/unknown classification semantics and downstream confidence behavior
are unchanged.

See `docs/STEP_192.md` for the exact invariant and regression scope.


## Canonical freshness execution-state integrity (Step 193)

Canonical `SourceFreshnessResult` records now reject
`status="usable"` when `freshness_executed=False`. A result cannot expose
usable freshness assessments and positive fresh/stale/unknown counts while
simultaneously claiming that freshness evaluation did not run.

The rule applies to direct typed construction and mapping/deserialization.
`empty` and `unavailable` results remain permitted to record
`freshness_executed=False`, because those states cannot contribute a positive
freshness signal and may legitimately represent skipped or unavailable work.

Existing evaluator outputs, Step-192 strict count types, Step-191 unknown-policy
semantics, Step-190 classification rules, and downstream confidence behavior
remain unchanged.

See `docs/STEP_193.md` for the exact invariant and regression scope.


## Canonical source-observation execution-state integrity (Step 194)

Canonical `SourceObservationResult` records now reject
`status="usable"` when `observation_executed=False`. A result cannot expose
usable source-observation records while simultaneously claiming that source
observation did not run.

The rule applies to direct typed construction, mapping/deserialization, and
mapping-shaped inputs consumed by `SourceFreshnessEvaluator`. `empty` and
`unavailable` observation results remain permitted to record
`observation_executed=False`, because they contain no usable observations and
cannot legitimately produce a positive downstream freshness signal.

Existing timestamp canonicalization, freshness classification, freshness count
integrity, and freshness execution-state integrity remain unchanged.

See `docs/STEP_194.md` for the exact invariant and regression scope.


## Canonical source-provenance execution-state integrity (Step 195)

Canonical `SourceProvenanceResult` records now reject
`status="usable"` when `provenance_executed=False`. A result cannot expose
usable source-provenance records while simultaneously claiming that provenance
assignment did not run.

The rule applies to direct typed construction, mapping/deserialization, and
mapping-shaped provenance consumed by `SourceObservationBuilder`. `empty`
and `unavailable` provenance results remain permitted to record
`provenance_executed=False`, because they contain no usable provenance records
and cannot legitimately drive a positive downstream observation/freshness
signal.

Existing source lineage, observation, freshness, and confidence semantics
remain unchanged.

See `docs/STEP_195.md` for the exact invariant and regression scope.


## Canonical claim-conflict execution-state integrity (Step 196)

Canonical `ClaimConflictResult` records now reject both `usable` and
`empty` results when `detection_executed=False`.

This is stricter than the provenance/observation/freshness execution rules
because an `empty` conflict result means conflict detection actually ran and
found zero candidate conflicts. Downstream confidence can treat that zero
conflict count as part of a supported result, so an empty result cannot safely
claim that detection never executed.

Only `unavailable` conflict results may explicitly record
`detection_executed=False`.

Existing deterministic conflict detection, provenance, freshness, and
confidence semantics remain unchanged.

See `docs/STEP_196.md` for the exact invariant and regression scope.


## Canonical claim-evidence linked-claim count integrity (Step 197)

Canonical `ClaimEvidenceLinkingResult` records now require
`linked_claim_count` to exactly match the number of distinct
case-insensitive claim texts represented by the canonical `links` collection.

This closes a confidence-integrity gap where a malformed linking result could
overstate linked-claim coverage—for example, one actual linked claim with
`linked_claim_count=2` and `claim_count=2`—and thereby appear to have 100%
claim-evidence coverage.

Multiple links for the same claim still count as one linked claim, matching the
existing production helper semantics. Empty link collections require a linked
claim count of zero.

See `docs/STEP_197.md` for the exact invariant and regression scope.


## Canonical claim-evidence linking execution-state integrity (Step 198)

Canonical `ClaimEvidenceLinkingResult` records now reject
`status="usable"` when `linking_executed=False`.

A usable linking result can provide positive claim-evidence coverage to the
confidence layer, so it cannot simultaneously claim that linking never ran.
`empty` and `unavailable` linking results remain permitted to record
`linking_executed=False` because they cannot produce full supported coverage.

Step-197 linked-claim count integrity, production linking behavior, and the
confidence formula remain unchanged.

See `docs/STEP_198.md` for the exact invariant and regression scope.


## Canonical claim-extraction execution-state integrity (Step 199)

Canonical `ClaimExtractionResult` records now reject
`status="usable"` when `extraction_executed=False`.

Usable extracted claims feed both claim-evidence linking and conflict
detection, so they cannot safely exist while the result claims extraction never
ran. `empty` and `unavailable` extraction results remain permitted to record
`extraction_executed=False` because they cannot produce positive claim
coverage.

Existing deterministic extraction, Step-197 count integrity, Step-198 linking
execution integrity, conflict behavior, and confidence semantics remain
unchanged.

See `docs/STEP_199.md` for the exact invariant and regression scope.


## Canonical evidence-quality usable-state integrity (Step 200)

Canonical `EvidenceQualityValidationResult` records now enforce the same
positive evidence-quality conditions used by the production validator.

A `status="usable"` result must have validation executed, at least one source,
content present, complete provenance, and no validation issues. This closes a
confidence-integrity gap where a malformed canonical quality result could claim
usable external evidence despite missing the conditions required by the actual
validator.

`insufficient` and `not_required` remain non-positive states and may
explicitly record `validation_executed=False`; neither can establish supported
external-evidence quality.

See `docs/STEP_200.md` for the exact invariant and regression scope.


## Canonical evidence-normalization consumption execution integrity (Step 201)

The canonical evidence-normalization consumption gate now rejects
`status="usable"` when `consumption_executed=False`.

That decision's `usable` field is the explicit orchestration gate into
evidence-quality validation, so a positive decision cannot claim that the
consumption evaluation never ran. Rejected decisions remain permitted to record
`consumption_executed=False` because they fail closed.

The legacy `EvidenceNormalizationConsumptionResult` adapter inherits the same
rule when `consumption_evaluated` is mapped into the canonical execution
field.

See `docs/STEP_201.md` for the exact invariant and regression scope.


## Canonical evidence-normalization execution-state integrity (Step 202)

Canonical `EvidenceNormalizationResult` records now reject
`status="completed"` when `normalization_executed=False`.

The immediate downstream `EvidenceNormalizationConsumer` now preserves its
legacy compact-dictionary behavior while reconstructing positive completed and
not-required inputs through the canonical `EvidenceNormalizationResult`
contract before classifying them. This prevents an explicit completed
non-executed mapping from bypassing the execution invariant without breaking
older callers that omit newer metadata.

Non-completed statuses keep their existing execution flexibility, while normal
production normalization continues to record execution as `True`.

See `docs/STEP_202.md` for the exact invariant and regression scope.


## Canonical retrieval-result consumption state integrity (Step 203)

The canonical retrieval-consumption gate now enforces the complete positive
state used by production orchestration.

A `status="usable"` decision must have executed consumption, may correspond
only to `completed` or `not_required` retrieval, and cannot carry a rejection
reason. Rejected decisions must remain non-usable and carry a nonempty reason;
they may explicitly record `consumption_executed=False` because they fail
closed.

This aligns the Step-151 canonical contract with the actual Step-85 production
consumer and prevents contradictory dependency output from authorizing evidence
normalization.

See `docs/STEP_203.md` for the complete state matrix and regression scope.


## First-class Reality Entity foundation (Step 204)

Reality States now include a canonical top-level `entity` object.

Both Reality State endpoints accept an optional explicit entity name. When a
caller supplies `"entity": "Company X"`, the resulting snapshot records:

```json
{
  "status": "specified",
  "name": "Company X",
  "identification_method": "explicit_input"
}
```

When no entity is supplied, the snapshot records an explicit `unspecified`
entity rather than trying to infer identity from task text.

This is the foundation for future entity resolution, structured claim subjects,
persistent entity histories and a Reality Graph. Step 204 does not yet perform
NER, heuristic parsing, embedding matching, LLM entity extraction or
entity-aware retrieval rewriting.

See `docs/STEP_204.md` for the complete contract and compatibility rules.


## Reality State verification metadata foundation (Step 205)

Canonical Reality States now include a top-level `verification` object with a
system-generated UTC `verified_at` timestamp when deterministic signal-snapshot
assembly completes.

```json
{
  "status": "completed",
  "verified_at": "2026-01-02T03:04:05Z",
  "verification_method": "deterministic_pipeline_snapshot",
  "reason": null
}
```

This timestamp means the Reality Layer completed this snapshot's evidence and
signal assembly. It does **not** mean source publication time, event time,
source-observation time, independent fact-check time, or guaranteed factual
truth.

Legacy snapshots without verification metadata normalize to an explicit
`not_completed` state instead of receiving invented historical timestamps.
Verification is output-only; API callers cannot submit or override it.

See `docs/STEP_205.md` for the complete timestamp and trust semantics.


## Canonical structured claim representation foundation (Step 206)

Every `EvidenceClaim` now carries a canonical `semantic_structure` object.

The current deterministic sentence extractor is still deliberately honest about
its limits and emits:

```json
{
  "status": "unstructured",
  "subject": null,
  "predicate": null,
  "object": null,
  "structuring_method": "not_attempted",
  "reason": "semantic_structuring_not_attempted"
}
```

The same contract also defines a validated provider-neutral `structured`
subject/predicate/object form for future semantic NLP/ML/LLM components.

Step 206 does not infer semantic parts from task text, does not bind the Step-204
Reality Entity to every claim automatically, and does not change linking,
conflict, freshness or confidence behavior.

See `docs/STEP_206.md` for the complete semantic and compatibility boundary.

## Optional semantic claim structuring boundary (Step 207)

The candidate-claim extractor now includes a **provider-neutral semantic
structuring boundary**. By default it still does **not** infer subject,
predicate, or object. Existing Reality State responses remain unchanged
(`semantic_structure.status = "unstructured"` and
`reason = "semantic_structuring_not_attempted"`).

A trusted in-process adapter can be injected through
`EvidenceClaimExtractor(semantic_structurer=...)` using the existing
`OrchestrationDependencies` composition mechanism. Each adapter receives
the claim text and its *complete, deduplicated source reference tuple*, and
its output must pass the Step-206 semantic-structure contract.

Invalid or failing adapters cannot create a structured claim: they yield
explicit `unstructured` results with a failure reason. An adapter returning
`None` is separately marked `semantic_structuring_no_result`.

The boundary validates data integrity, **not semantic accuracy or factual
truth**. Step 207 adds no actual Hugging Face, ML, or LLM model and exposes
no model-selection input to external API callers.

See `docs/STEP_207.md` for integration, failure behavior, and regression
details.

## Submitted-evidence semantic structuring integrity (Step 208)

Source-scoped developer-submitted evidence now uses **one global candidate-claim
extraction pass** before the optional Step-207 semantic structurer executes.
Previously, duplicate claims across documents were merged after per-document
semantic structuring, which could silently discard valid structured metadata.
The corrected path deduplicates first, preserves complete `source_refs`, and
calls an injected semantic adapter only once per unique claim.

The preexisting **2,000 unique candidate claims** limit is checked before
optional model execution. An over-limit bundle still yields
`submitted_claim_limit_exceeded` with no partial claim graph. There is no
change to the external request/response schema or the default
`unstructured` behavior.

See `docs/STEP_208.md` for the verified bug, fix, and regression tests.

## Semantic structuring method integrity and bounded metadata (Step 209)

The canonical semantic-structure contract now rejects a `structured` claim
whose `structuring_method` normalizes to the reserved `not_attempted` marker
(including surrounding whitespace). Adapter-provided metadata is bounded:
normalized `structuring_method` is at most **256 characters** and normalized
`unstructured.reason` is at most **1,024 characters**.

These rules apply to typed claims, legacy-compatible mapping reconstruction,
optional in-process semantic adapter output, and Reality State JSON.
Invalid adapter output remains explicitly `unstructured` with
`semantic_structuring_failed` rather than leaking bad metadata.
The default behavior still performs no ML/LLM inference.

See `docs/STEP_209.md` for exact invariants and regression tests.

## Optional semantic-adapter input bound (Step 210)

Candidate claims still preserve the complete source evidence, but the
**optional configured semantic structurer** is not invoked for a candidate
claim exceeding **10,000 characters**. Its claim remains in the Reality
State, with all source references and explicit semantic result
`unstructured` / `semantic_structuring_input_too_long`.

The bound is checked *after* cross-source claim deduplication and existing
global claim limits and *before* calling an injected adapter. In-bounds
claims remain eligible for structuring. No text is silently truncated.

The default no-model extractor retains the original
`semantic_structuring_not_attempted` reason even for long claims. This is
a character bound, not a model-specific context/token budget and does not
add or activate any NLP, Hugging Face, ML, or LLM model.

See `docs/STEP_210.md` for the verified resource gap, exact behavior,
and validation coverage.

## Optional semantic-adapter claim-budget integrity (Step 211)

`EvidenceClaimExtractor` now enforces the existing **2,000 unique
candidate-claim limit** before invoking any **configured optional semantic
structurer** for both `completed` and `usable` evidence. The `usable`
path previously bypassed that invocation budget and could execute a
configured adapter 2,001+ times.

At the first over-budget unique claim, extraction returns
`unavailable` / `retrieved_claim_limit_exceeded` with zero claims,
zero adapter calls and no partial claim graph. The submitted-evidence
bundle retains its existing `submitted_claim_limit_exceeded` translation.

**Compatibility:** The older generic `usable` extractor path *without*
an injected semantic adapter intentionally still accepts more than 2,000
claims, as established by Steps 184–185. No default model execution,
public API, provider, or other resource limit is changed.

See `docs/STEP_211.md` for the exact state matrix and tests.

## Canonical retrieved-source identity (Step 212)

Source URLs now have **leading and trailing whitespace trimmed consistently**
across configured HTTP retrieval, provider-neutral evidence normalization,
candidate claims, source provenance SHA-256 identity, and source observation
matching. Claim-to-evidence links therefore use the same URI identity as
their provenance records.

Whitespace variants of the same URL are rejected as duplicates before
claim extraction at the retrieval boundary, rather than being counted as
independent publishers or evidence sources. Submitted-evidence URIs were
already trimmed and retain their prior behavior.

This step does **not** lowercase addresses, follow redirects, merge distinct
URLs, or verify that a publisher is authentic. No AI model or new API is added.
See `docs/STEP_212.md` for implementation details and test cases.

## Canonical source-provenance identity coherence (Step 213)

The typed and mapping-shaped `SourceProvenance` contracts now require
**`source_ref` and `uri` to identify the same canonical, whitespace-trimmed
URL**. A `SourceProvenanceResult` must also have **unique source IDs and
source references** across its records.

This closes the low-level path that could reintroduce contradictory or
duplicate identities after the Step 212 retrieval normalization boundary.
The normal builder already emits coherent SHA-256 source identities and
needs no new logic. Historical direct typed fixture IDs remain compatible,
and output schemas do not change.

This validates **internal source identity consistency**, not source
authenticity or the factual truth of evidence.

See `docs/STEP_213.md` for acceptance cases, error handling, and
regression tests.

## Unique source observations and freshness assessments (Step 214)

Canonical `SourceObservationResult` and `SourceFreshnessResult` records now
require **each source ID to appear at most once per result**. This prevents
duplicate observations or contradictory fresh/stale assessments from being
counted as multiple independent sources in a single Reality State snapshot.

The checks apply to direct typed construction and mapping deserialization,
and prevent duplicate observation input from reaching freshness evaluation.
Existing source IDs, timestamps, age-window policies, output schemas and
empty/unavailable outcomes remain unchanged. Multiple observations of the
same source in **different snapshots** remain possible; this is not a
history store.

See `docs/STEP_214.md` for the verified gap and regression coverage.

## Canonical claim–evidence link identity integrity (Step 215)

The canonical `ClaimEvidenceLink` contract now requires a trimmed
`source_ref`, matching Steps 212–213 source provenance identity. The
`ClaimEvidenceLinkingResult` contract rejects duplicate
`(claim_text.casefold(), source_ref)` pairs, matching the existing
production linker's deduplication rules. Direct typed and mapping-shaped
inputs therefore cannot inflate `link_count` by repeating an identical
claim–source relationship.

One claim may still have distinct links to multiple sources, and one
source may support multiple distinct claims. Existing API output,
`linked_claim_count`, normal linking behavior, and unsupported/empty
link states remain unchanged.

These checks establish structural consistency only—not independent
source authenticity or factual truth. See `docs/STEP_215.md`.

## Canonical candidate-conflict identity integrity (Step 216)

The canonical `ClaimConflictResult` now rejects repeated unordered,
case-insensitive claim-text pairs. Direct or mapping-shaped results
cannot treat reversed or differently capitalized copies of one candidate
contradiction as separate conflicts and inflate `conflict_count`.
`ClaimConflict` also requires trimmed source references, agreeing with
the existing canonical provenance and claim–evidence link rules.

The production detector already deduplicates these pairs; its
**explicit-negation-only** logic and all public API fields remain
unchanged. This is structural consistency, not general semantic
conflict recognition or independent factual verification.

See `docs/STEP_216.md` for details and regression coverage.

## Measured Reality State quality baseline (Step 217)

The old `backend/app/evaluation/benchmark.py` remains an **orchestration
structure** benchmark. Step 217 introduces a **separate evidence-quality
baseline** at `backend/app/evaluation/reality_state_quality_benchmark.py`.

It evaluates 48 clearly labeled **controlled hypothetical** service-status
cases spanning true-looking evidence, deliberately misleading source
statements, exact negation, semantic paraphrase disagreement, stale
observations, and absent freshness policy. All URLs are under
`fixtures.example.test`. **These are simulated reference-world labels,
not independently verified real-world statements**.

The fixed oracle is never passed to the production processing pipeline.
The runner measures claim text and source matching, detected conflict
pairs, false `supported` status on cases requiring abstention, and
safe abstention, including a per-scenario breakdown. It preserves
negative quality results rather than redefining `supported` as
factual truth.

```bash
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.reality_state_quality_benchmark --output /tmp/step217-full.json
```

GitHub Actions executes the quality summary after full `pytest`. This
baseline does **not** change the production API or imply field accuracy.
Independently captured real-source evidence and blinded annotation are
still necessary before claiming real-world performance. See
`docs/STEP_217.md` and `docs/STEP_217_BASELINE.md`.

## Official-publisher-anchored historical evidence quality replay (Step 218)

Step 218 builds on, but does **not replace**, the Step 217 fictional baseline.
The new `backend/app/evaluation/official_source_quality_benchmark.py`
replays **48 cases grounded in eight manually checked official
historical software-release announcement pages** from Python, Node.js,
Go, Rust and Kubernetes. The short release-date descriptions are
reviewer-written summaries, **not raw archived publisher text**.

Each publisher anchor is tested for correct relevance, synthetic
URL-content tampering, wrong-topic official evidence, synthetic
explicit contradiction, old observation metadata and missing freshness
policy. The benchmark reports wrong-topic support, general false
support and abstention while keeping **all** human/assistant-generated
gold labels out of the production pipeline.

```bash
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --output /tmp/step218-cases.json
```

The runner is fully offline, with simulated observation times.
Original publishers are cited in `docs/STEP_218.md`; **no automatic
URL-to-content authenticity verification, raw capture, independent
blinded human annotation, field accuracy or live retrieval is claimed**.
See `docs/STEP_218_BASELINE.md` for the actual observed results.

## Conservative explicit-entity evidence relevance (Step 219)

The Step 218 quality replay revealed eight of eight **wrong-topic
official-source** cases incorrectly marked `supported`. Step 219
introduces a narrow production gate: if the caller provides an explicit
`entity`, **every linked claim must contain that entity's full textual
identity** before Reality State status can be `supported`. Matching
is Unicode case-insensitive with whole-identifier and version-suffix
boundaries. Nonmatching cases become `uncertain` with
`explicit_entity_not_aligned_with_all_linked_claims`.

Both the developer-submitted and retrieval-backed Reality State paths
enforce the gate. Callers without an explicit entity keep historical
behavior. The `explicit_entity_text_alignment_only` signal means
**literal name matching only**: it is not a claim of semantic entailment,
real URL-content authentication or factual correctness. Step 218's
historical 40% false-support baseline is **preserved** and a separately
versioned Step 219 scorecard documents measured improvement and
remaining failures.

See `docs/STEP_219.md` and `docs/STEP_219_SCORECARD.md`.

## Opt-in backend-observed source text assurance (Step 220)

The default submitted-evidence endpoint treats submitted URLs and claims
as **unverified reported evidence**. Step 220 adds the opt-in flag
`require_independent_source_text_match: true` to require the **entire
submitted excerpt** to occur in text independently returned by a
**server-installed** reader, matched to the exact canonical source URI.

When no independent reader is configured (the prototype default), or
when any observed URI/body/quote comparison fails, the status becomes
`uncertain` and `evidence.independent_source_text_assurance` explains
why. Only a backend-owned configured reader can produce
`exact_text_observed`; no client-provided hash or attestation can do so.
Other confidence/freshness/entity constraints remain in force.

A separately measured Step 220 **simulated observer** benchmark tests
this gate on Step 218's 48 scenarios without pretending that
reviewer-written summaries are original publisher text. The simulated
reader is **not** a configured production publisher fetcher.

```bash
python -m backend.app.evaluation.independent_source_assurance_benchmark
```

Text presence is **not source/publisher authentication, entailment,
world truth, or independent corroboration**. A genuine, hardened
source reader must still be implemented and deployed by the backend
operator. See `docs/STEP_220.md` and `docs/STEP_220_SCORECARD.md`.

## Real allowlisted HTTPS source reading (Step 221)

Strict evidence mode can now use real, independently obtained source
text when a **backend operator** sets
`ARL_INDEPENDENT_SOURCE_ALLOWED_URLS` to a JSON array of exact HTTPS URLs.
No setting means no reader and a fail-closed `uncertain` result.

The reader resolves and validates publicly routable addresses, pins
the TCP connection to the checked IP, uses standard verified TLS/SNI,
rejects redirects and unsupported responses, bounds received bytes,
and extracts visible HTML/plain text. Successful strict comparison
records a digest of retrieved original HTTP body bytes and a
server-observed UTC timestamp. No API caller can extend the URL allowlist.

This is a real network-capable reader but **not an independently audited
publisher-authenticity service**. CI uses fake transports, not live site
capture. Source text presence does not prove factual truth or entailment.
See `docs/STEP_221.md` for configuration, safeguards, constraints and
the explicit need for a permitted real-network smoke test.
