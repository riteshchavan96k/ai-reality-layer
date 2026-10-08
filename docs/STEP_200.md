# Step 200 — Canonical Evidence-Quality Usable-State Integrity

## Objective

Ensure a canonical evidence-quality validation result cannot claim usable
external evidence unless all of the positive evidence-quality conditions used
by the production validator are actually present and validation is recorded as
executed.

Step 154 and later downstream hardening made claim extraction, linking,
conflict detection, provenance, observation, freshness, and confidence
contracts increasingly strict. The next upstream positive signal consumed
directly by confidence is `EvidenceQualityValidationResult`.

## Verified gaps

Before Step 200, the canonical result could accept contradictory positive
states such as:

```text
status = "usable"
usable = True
source_count = 1
has_content = True
provenance_complete = True
issues = []
validation_executed = False
```

It could also accept structurally impossible "usable" combinations that the
production `EvidenceQualityValidator` never emits:

```text
status = "usable"
usable = True
source_count = 0
```

```text
status = "usable"
usable = True
has_content = False
```

```text
status = "usable"
usable = True
provenance_complete = False
```

or:

```text
status = "usable"
usable = True
issues = ["validation issue"]
```

These states matter because `RealityConfidenceSignalAggregator` treats
`evidence_quality.status == "usable"` as the positive evidence-quality gate.
It does not recalculate structural quality from source/content/provenance
details.

A malformed canonical evidence-quality result could therefore overstate
grounding quality and contribute to a supported Reality State.

## Canonical usable-state invariant

The production evidence-quality validator already defines usable evidence as:

- at least one source exists;
- content is present;
- provenance is complete;
- no validation issues exist;
- the validation stage actually ran.

Step 200 makes the canonical contract enforce the same positive state.

For `status == "usable"`:

```text
usable is True
source_count > 0
has_content is True
provenance_complete is True
issues == []
validation_executed is True
```

The existing relationship also remains:

```text
status != "usable"
→ usable is False
```

## Why insufficient and not_required are not over-constrained

Step 200 deliberately does not require
`validation_executed=True` for `insufficient` or `not_required`.

Those states are non-positive at the confidence boundary:

- `insufficient` produces evidence-quality-insufficient confidence;
- `not_required` produces external-evidence-not-required / insufficient
  confidence.

They therefore cannot falsely establish supported external-evidence quality.

The production helper methods still emit `validation_executed=True` for
their current normal paths, so normal behavior remains unchanged.

## Implementation

`EvidenceQualityValidationResult.__post_init__()` now preserves all existing
type/status/usability checks and additionally requires a usable result to have:

- `validation_executed=True`;
- `source_count > 0`;
- `has_content=True`;
- `provenance_complete=True`;
- no validation issues.

No fields are coerced or inferred.

## Mapping and normalization integrity

`EvidenceQualityValidationResultNormalizer` reconstructs mapping-shaped input
through `EvidenceQualityValidationResult`.

Therefore the same usable-state invariant applies to mapping-shaped results.

A mapping cannot claim positive evidence quality while denying validation or
carrying missing source/content/provenance conditions.

## Confidence integrity

The confidence algorithm is unchanged.

A legitimate executed usable evidence-quality result continues to participate
in supported confidence when linking, freshness, and conflict signals are
healthy.

An insufficient or not-required evidence-quality result remains non-supported.

The protected boundary is:

```text
normalized evidence
→ evidence-quality validation
→ canonical usable evidence-quality state
→ confidence signals
→ Reality State
```

## Compatibility

Normal production behavior is unchanged.

`EvidenceQualityValidator.validate_result()` already emits `usable` only
when:

- source count is non-zero;
- content is present;
- provenance is complete;
- no issues were produced.

Its normal helper outputs also retain `validation_executed=True`.

Step 200 preserves:

- Steps 152–153 evidence-normalization contract boundaries;
- Step 199 claim-extraction execution integrity;
- Step 198 linking execution integrity;
- Step 197 linked-claim count integrity;
- Step 196 conflict execution integrity;
- Steps 188–195 provenance/observation/freshness integrity;
- the existing confidence formula and policy;
- APIs, retrieval behavior, and resource limits.

## Regression coverage

`backend/tests/test_step200.py` covers:

- rejection of usable non-executed evidence quality;
- mapping/normalizer rejection;
- valid executed usable state;
- rejection of non-boolean execution values;
- deliberate non-executed insufficient/not-required compatibility;
- existing helper execution semantics;
- production validator usable/insufficient/not-required behavior;
- supported confidence compatibility for a legitimate usable result;
- insufficient/not-required inability to become supported;
- preservation of status/usability consistency;
- rejection of usable zero-source state;
- rejection of usable missing-content state;
- rejection of usable incomplete provenance;
- rejection of usable results carrying validation issues;
- helper inheritance of the complete usable-state invariant.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation commit on `main`,
and the final synchronized `main` status commit.

## Deliberate non-goals

Step 200 does not change evidence-normalization logic, evidence-quality scoring,
claim extraction, linking, conflict detection, freshness, or the confidence
formula.

It does not add semantic evidence scoring, calibrated probability, LLM
judging, embeddings, publication-time inference, source-authenticity
verification, factual-truth scoring, new providers, persistence,
authentication, UI, monitoring, or autonomous behavior.
