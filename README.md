# ai-reality-layer
AI Reality Layer — infrastructure for giving autonomous AI systems continuously verified information about the world before they reason, decide, or act.

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
