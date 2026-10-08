# Step 202 — Canonical Evidence-Normalization Execution-State Integrity

## Objective

Ensure completed normalized evidence cannot enter the downstream consumption
gate while simultaneously claiming that normalization did not execute.

Step 152 established the canonical `EvidenceNormalizationResult` validation
entry point. Step 201 hardened the downstream evidence-normalization
consumption decision. The remaining upstream gap was the relationship between
`status="completed"` and `normalization_executed`.

## Verified gap

Before Step 202, this canonical state was accepted:

```text
status = "completed"
sources = [normalized source]
content = "..."
source_count = 1
has_content = True
normalization_executed = False
```

That state is contradictory: it exposes completed normalized evidence while
claiming that the normalization stage did not execute.

The orchestration pipeline passes the normalized result into
`EvidenceNormalizationConsumer`, whose positive decision then gates entry
into evidence-quality validation.

Without Step 202, completed/non-executed evidence could therefore reach:

```text
evidence normalization
→ normalization consumption
→ evidence quality
→ claim extraction / provenance / freshness
→ confidence
→ Reality State
```

## Canonical execution invariant

Step 202 adds:

```text
status == "completed"
→ normalization_executed is True
```

Existing type, source-count, source-shape, content, and content-presence
invariants remain intact.

## Why other statuses are not assigned new execution semantics

Step 202 deliberately does not force a new execution meaning onto:

- `not_required`;
- `invalid_evidence`;
- `unknown`.

Those states do not represent completed usable external evidence.

`not_required` may legitimately represent a path where normalization work was
not necessary. `invalid_evidence` and `unknown` are rejected by the
downstream evidence-normalization consumer.

The current production normalizer still records
`normalization_executed=True` on its normal outputs, including these statuses.
Step 202 simply avoids inventing stricter semantics than are needed to close the
positive completed-evidence contradiction.

## Consumption-boundary enforcement

A dataclass invariant alone would be bypassable if callers supplied a raw
mapping directly to `EvidenceNormalizationConsumer`.

Step 202 therefore also makes that consumer validate its input through
`EvidenceNormalizationResult.validate()` before interpreting status, sources,
or content.

The boundary is now:

```text
normalization result
→ canonical EvidenceNormalizationResult validation
→ normalization consumption classification
→ Step-201 canonical consumption validation
```

This means a mapping with `status="completed"` and
`normalization_executed=False` is rejected before it can be classified as
usable.

The consumer now also accepts an existing canonical
`EvidenceNormalizationResult` directly because the canonical validator
already supports typed objects.

## Production compatibility

`RetrievalEvidenceNormalizer.normalize_result()` already records
`normalization_executed=True` for completed output.

Its current invalid-evidence and not-required outputs also retain their existing
execution value of `True`.

The normal orchestration path therefore does not change.

## Regression coverage

`backend/tests/test_step202.py` covers:

- direct rejection of completed/non-executed normalization;
- canonical mapping rejection;
- `from_mapping()` rejection when false execution is explicit;
- valid completed/executed normalization;
- non-boolean execution rejection;
- deliberate preservation of non-completed execution flexibility;
- consumer rejection of completed/non-executed mappings;
- consumer enforcement of the complete canonical mapping shape;
- consumer acceptance of canonical typed and mapping inputs;
- not-required downstream compatibility;
- invalid/unknown downstream rejection;
- production normalizer completed/invalid/not-required behavior;
- source-count and content-presence non-regression;
- Step-201 downstream consumption execution integrity.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation commit on `main`,
and the final synchronized `main` status commit.

## Deliberate non-goals

Step 202 does not redesign normalization logic, evidence quality, claim
extraction, provenance, freshness, conflict detection, confidence, or
retrieval.

It does not change `from_mapping()` compatibility defaults when execution
metadata is omitted; explicit canonical `validate()` input still requires the
canonical fields.

It also does not add semantic evidence scoring, LLM judging, embeddings,
publication-time inference, source-authenticity verification, factual-truth
scoring, persistence, authentication, UI, monitoring, or autonomous behavior.
