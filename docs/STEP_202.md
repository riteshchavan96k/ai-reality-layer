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

The consumer has an older compatibility contract, established by Steps 88–89,
that accepts compact dictionaries containing only status, sources, and content
and returns structured rejection reasons for malformed source/content shapes.

Step 202 preserves that behavior while closing the execution bypass:

1. existing input-type and source/content checks run first;
2. a completed or not-required mapping is reconstructed through
   `EvidenceNormalizationResult.from_mapping()`;
3. explicit canonical metadata, including `normalization_executed`, is then
   validated by the canonical result contract;
4. only after that may the consumer emit a positive consumption decision.

The boundary is now:

```text
legacy or canonical normalized-evidence input
→ compatibility shape checks
→ canonical EvidenceNormalizationResult reconstruction
→ normalization consumption classification
→ Step-201 canonical consumption validation
```

A mapping with `status="completed"` and
`normalization_executed=False` is rejected before it can be classified as
usable, while historical compact mappings without newer metadata remain
compatible.

The consumer also accepts an existing canonical
`EvidenceNormalizationResult` directly by serializing it through the same
classification path.

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
- preservation of legacy compact completed mappings;
- preservation of legacy invalid-source and invalid-input behavior;
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
