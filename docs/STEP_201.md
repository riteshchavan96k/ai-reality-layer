# Step 201 — Canonical Evidence-Normalization Consumption Execution-State Integrity

## Objective

Ensure the canonical decision that permits normalized evidence to enter
evidence-quality validation cannot claim usability while simultaneously
claiming that the consumption decision was not executed.

Step 153 established the canonical
`EvidenceNormalizationConsumption` boundary. Its
`consumption_executed` field was type-checked, but a positive decision could
still carry `False`.

## Verified gap

Before Step 201, this canonical state was accepted:

```text
status = "usable"
evidence_status = "completed"
usable = True
consumption_executed = False
```

The orchestration pipeline gates downstream evidence processing on
`evidence_consumption.usable`. It does not separately check
`consumption_executed`.

A malformed positive decision could therefore say that normalized evidence is
approved for downstream use even while claiming that the consumption decision
never ran.

The downstream path is:

```text
evidence normalization
→ normalization consumption decision
→ evidence quality
→ claims / provenance / freshness
→ confidence
→ Reality State
```

## Canonical invariant

Step 201 adds:

```text
status == "usable"
→ consumption_executed is True
```

The existing invariant remains:

```text
status == "usable"
→ usable is True
```

and:

```text
status == "rejected"
→ usable is False
```

## Why rejected remains flexible

A rejected consumption decision is fail-closed. It prevents normalized evidence
from entering the positive downstream path.

Step 201 therefore deliberately permits a rejected decision to record
`consumption_executed=False`, allowing future callers to represent a skipped
or unavailable consumption evaluation without turning it into positive
evidence.

Normal production rejection helpers continue to emit
`consumption_executed=True`.

## Legacy result adapter

The repository still contains the older
`EvidenceNormalizationConsumptionResult` contract with
`consumption_evaluated`.

`EvidenceNormalizationConsumptionNormalizer` maps that field into
`consumption_executed`.

Step 201 therefore also closes the legacy-adapter path: a legacy result cannot
be positive/usable with `consumption_evaluated=False` and then normalize into
a positive canonical consumption decision.

## Production compatibility

`EvidenceNormalizationConsumer` already records evaluation as executed for its
current paths:

- completed non-empty evidence → usable;
- not-required evidence → usable;
- invalid evidence → rejected;
- empty completed evidence → rejected;
- unknown evidence → rejected.

Those normal paths remain unchanged.

## Scope boundary

Step 201 intentionally does **not** change
`EvidenceNormalizationResult.normalization_executed`.

That upstream result contract remains a separate boundary. This step hardens
the explicit Step-153 consumption gate first because the orchestration pipeline
uses its `usable` field directly to decide whether evidence may proceed.

Step 201 also does not change evidence-quality semantics, claim extraction,
linking, conflict detection, provenance, freshness, or confidence.

## Regression coverage

`backend/tests/test_step201.py` covers:

- direct rejection of usable non-executed consumption;
- mapping validation rejection;
- normalizer rejection;
- legacy consumption-result adapter rejection;
- valid executed usable consumption;
- non-boolean execution rejection;
- deliberate rejected/non-executed compatibility;
- existing helper execution semantics;
- production consumer completed path;
- production consumer not-required path;
- production consumer invalid-evidence path;
- empty completed evidence rejection;
- preservation of status/usability integrity;
- explicit proof that upstream normalization execution semantics are unchanged.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation commit on `main`,
and the final synchronized `main` status commit.

## Deliberate non-goals

Step 201 does not redesign evidence normalization, evidence quality, retrieval,
claim extraction, confidence, or orchestration.

It does not add semantic evidence evaluation, LLM judging, embeddings,
publication-time inference, source-authenticity verification, factual-truth
scoring, persistence, authentication, UI, monitoring, or autonomous behavior.
