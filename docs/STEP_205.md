# Step 205 — Reality State Verification Metadata Foundation

## Objective

Add the missing MVP verification-time metadata to every canonical Reality
State without confusing pipeline completion with source publication time,
source observation time, event occurrence time, or factual truth.

The MVP specification has always listed "last verification time" in the
structured Reality State output. Through Step 204, the repository had no
verification metadata implementation.

Step 205 establishes that foundation before later semantic claim extraction,
entity resolution, persistence, temporal versioning, or continuous updates.

## Why this step follows Entity

Step 204 introduced first-class explicit entity identity.

The two remaining immediate MVP semantic gaps were:

1. claims are still free-form sentence candidates rather than structured
   subject/relation/object records; and
2. Reality States have no verification-time metadata.

Structured claim extraction requires a reliable semantic strategy. Forcing
subject/relation/object parsing with brittle deterministic heuristics would
lower quality and create false semantic certainty.

Verification-pass metadata, by contrast, can be defined precisely and
deterministically today.

## Verification semantics

Step 205 defines:

> `verified_at` is the UTC time when AI Reality Layer completed assembly of
> this deterministic Reality State signal snapshot.

It does **not** mean:

- when a source was published;
- when the underlying real-world event happened;
- when a retrieval provider observed a source;
- when a caller observed submitted evidence;
- when a publisher authenticated a document;
- when a fact became objectively true;
- when an independent fact checker certified a claim;
- a guarantee that the Reality State is factually correct.

The Reality Layer may complete verification and still conclude that the state
is `uncertain`, `insufficient`, or `unavailable`.

## Canonical RealityVerification

Step 205 adds:

`backend/app/reality/reality_verification.py`

The immutable contract has:

- `status`: `completed` or `not_completed`;
- `verified_at`: canonical UTC ISO-8601 timestamp or `None`;
- `verification_method`: `deterministic_pipeline_snapshot` or
  `not_completed`;
- `reason`: absent for completed verification, required when not completed.

### Completed state

A completed verification requires:

```text
status = completed
verified_at = timezone-aware canonical UTC timestamp
verification_method = deterministic_pipeline_snapshot
reason = None
```

### Not-completed state

A not-completed verification requires:

```text
status = not_completed
verified_at = None
verification_method = not_completed
reason = non-empty string
```

No timestamp is invented for a verification pass that did not complete.

## Timestamp validation

Verification timestamps:

- must be strings;
- must be non-empty;
- are bounded to 64 characters;
- must parse as ISO-8601;
- must include a timezone;
- cannot be in the future;
- are normalized to UTC with a `Z` suffix.

This keeps the canonical timestamp representation aligned with the project's
existing source-observation timestamp discipline while preserving different
semantics.

## Verification clock

`RealityStateBuilder` now accepts an optional clock dependency.

The production default is the current timezone-aware UTC time.

Tests can inject a deterministic clock, which makes verification metadata
repeatable and prevents time-dependent test flakiness.

A clock must return a timezone-aware `datetime`. Naive datetimes and
non-datetime values fail closed.

## Assembly timing

The builder creates `RealityVerification.completed(...)` only when final
Reality State assembly occurs after the already-computed:

- evidence quality;
- claim extraction;
- claim/evidence linking;
- source provenance;
- source observation;
- freshness;
- conflict detection;
- confidence signals.

Therefore `verified_at` means the deterministic Reality State signal snapshot
has been assembled.

It does not mean later model execution or the broader `/solve` orchestration
has completed.

## Reality State integration

Canonical Reality State output now includes:

```text
Reality State
├── status
├── task
├── entity
├── verification
├── evidence
├── claims
├── claim_evidence_linking
├── source_provenance
├── source_observation
├── freshness
├── conflicts
└── confidence_signals
```

The new defaulted domain field is appended after the existing defaulted fields
in the dataclass constructor, preserving historical positional constructor
meaning.

## Legacy compatibility

Older mapping-shaped Reality States that do not contain `verification` do not
receive a fabricated historical timestamp.

They normalize to:

```json
{
  "status": "not_completed",
  "verified_at": null,
  "verification_method": "not_completed",
  "reason": "verification_metadata_unavailable"
}
```

This is intentionally conservative.

Older direct `RealityState(...)` construction that omits verification receives
the same safe default.

## Unavailable Reality States

Reality State status and verification status answer different questions.

For example:

```text
Reality State status = unavailable
verification status = completed
```

is valid when the deterministic pipeline executed successfully and concluded
that evidence/confidence was unavailable.

By contrast, if the pipeline cannot assemble a canonical Reality State at all,
fallback output uses:

```text
verification status = not_completed
verified_at = None
```

with an explicit reason.

## API integration

`RealityStateResponse` now contains typed `RealityVerificationResponse`.

Verification is output metadata only.

Neither:

- `RealityStateRequest`; nor
- `EvidenceRealityStateRequest`

allows callers to supply or override `verification` or `verified_at`.

That prevents callers from forging the system's verification-completion time.

OpenAPI exposes verification only on the Reality State response.

## Relationship to source timestamps

Source observation time and Reality verification time remain separate.

Example:

```text
source observed_at = 2026-01-01T00:00:00Z
Reality verified_at = 2026-01-02T03:04:05Z
```

The first describes the source observation metadata.

The second describes when the Reality Layer assembled the evidence-backed
snapshot.

Neither is automatically a publication timestamp or factual-truth timestamp.

## Regression coverage

`backend/tests/test_step205.py` covers:

- canonical completed verification;
- timezone normalization to UTC;
- blank, malformed, naive, future, and oversized timestamp rejection;
- canonical not-completed state;
- completed/reason contradiction rejection;
- not-completed/timestamp contradiction rejection;
- required not-completed reason;
- mapping validation;
- legacy Reality State mappings without verification;
- historical direct Reality State construction;
- fixed-clock builder stamping;
- naive and non-datetime clock rejection;
- unavailable Reality State with completed verification;
- retrieval-backed verification metadata;
- submitted-evidence verification metadata;
- explicit separation from source observation time;
- output-only request semantics;
- typed response contract;
- OpenAPI output exposure;
- canonical serialization placement.

Historical exact-shape regressions are updated only where Step 205
intentionally adds the new top-level response field.

## MVP significance

Step 205 implements the MVP's missing verification-time foundation without
claiming semantic truth verification.

This prepares future work on:

- persisted Reality State versions;
- per-entity verification history;
- change detection;
- refresh scheduling;
- temporal diffs;
- event generation;
- continuous updates.

Those capabilities are not bundled into Step 205.

## Deliberate non-goals

Step 205 does not add:

- factual truth certification;
- source authenticity verification;
- publication-time extraction;
- event-time extraction;
- semantic claim parsing;
- entity resolution;
- persistence;
- Reality State version history;
- scheduled refresh;
- continuous monitoring;
- webhooks;
- knowledge graphs;
- NER;
- embeddings;
- ML/DL;
- LLM judging.

Those require separate design and validation.
