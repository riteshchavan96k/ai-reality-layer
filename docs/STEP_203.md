# Step 203 — Canonical Retrieval-Result Consumption State Integrity

## Objective

Harden the final retrieval-consumption gate before evidence normalization so a
canonical decision cannot authorize downstream evidence processing while its
own execution state, retrieval status, or reason metadata contradict that
authorization.

Step 150 hardened the retrieval-result envelope itself. Step 151 added the
canonical retrieval-consumption validation entry point. Steps 201–202 later
hardened the equivalent evidence-normalization gates. The retrieval-consumption
contract still had weaker semantic invariants than the production consumer.

## Verified gaps

Before Step 203, all of these canonical shapes were accepted:

```text
status = "usable"
retrieval_status = "completed"
usable = True
consumption_executed = False
```

```text
status = "usable"
retrieval_status = "failed"
usable = True
consumption_executed = True
```

```text
status = "usable"
retrieval_status = "blocked"
usable = True
consumption_executed = True
```

and:

```text
status = "usable"
retrieval_status = "completed"
usable = True
reason = "unexpected rejection reason"
```

A rejected decision could also omit its reason entirely.

Those states do not match the actual `RetrievalResultConsumer` semantics:

- completed non-empty retrieval → usable;
- not-required retrieval → usable;
- failed retrieval → rejected;
- blocked retrieval → rejected;
- empty completed retrieval → rejected.

The orchestration pipeline gates entry into evidence normalization directly on
`consumption.usable`, so the canonical decision itself must faithfully encode
that positive state.

## Canonical state invariants

Step 203 now enforces the following matrix.

For `status == "usable"`:

```text
usable is True
consumption_executed is True
retrieval_status in {"completed", "not_required"}
reason is None
```

For `status == "rejected"`:

```text
usable is False
reason is a non-empty string
```

Rejected decisions may still explicitly record
`consumption_executed=False`. That preserves a fail-closed representation for
a consumption decision that was skipped or unavailable without authorizing
downstream processing.

## Why completed and not_required are both usable

The existing retrieval contract has two positive downstream paths.

`completed` means retrieval executed and produced an envelope that can be
classified for evidence processing.

`not_required` means the task does not require external retrieval. It is
intentionally allowed through the retrieval-consumption gate so downstream
normalization can preserve the explicit not-required state rather than treating
it as retrieval failure.

Failed and blocked retrievals never represent usable retrieval evidence and
therefore cannot form a canonical usable consumption decision.

## Reason semantics

A usable decision is an authorization to proceed, so attaching a rejection
reason to it is contradictory.

A rejected decision is consumed by orchestration as a fail-closed path and its
reason is preserved in the invalid-evidence state. Requiring a non-empty reason
keeps that failure deterministic and diagnosable.

## Mapping and normalization integrity

`RetrievalResultConsumption.validate()` reconstructs mapping-shaped decisions
through the canonical constructor.

`RetrievalResultConsumptionNormalizer` delegates mappings to that validator.

Therefore the complete Step-203 state matrix applies equally to direct objects
and mapping-shaped dependency output.

## Production compatibility

`RetrievalResultConsumer` already emits states that satisfy Step 203:

- completed non-empty → usable, executed, no reason;
- not-required → usable, executed, no reason;
- failed → rejected with reason;
- blocked → rejected with reason;
- empty completed → rejected with reason.

The normal production orchestration path is therefore unchanged.

## Regression coverage

`backend/tests/test_step203.py` covers:

- direct usable/non-executed rejection;
- mapping and normalizer rejection;
- failed/blocked retrieval-status rejection for usable decisions;
- helper rejection of impossible positive statuses;
- usable/reason contradiction rejection;
- rejected missing/blank reason rejection;
- deliberate rejected/non-executed compatibility;
- valid completed and not-required usable decisions;
- non-boolean execution rejection;
- existing status/usability integrity;
- production completed/not-required/failed/blocked/empty classification;
- compatibility with Step-202 evidence normalization;
- rejected-helper compatibility.

Completion requires the complete GitHub-hosted backend compilation and pytest
suite to pass on the feature PR, the merged implementation commit on `main`,
and the final synchronized `main` status commit.

## Deliberate non-goals

Step 203 does not change retrieval execution, provider selection, provider
health/capability policy, evidence normalization, evidence quality, claim
extraction, provenance, freshness, conflict detection, confidence, or Reality
State semantics.

It also does not add new providers, semantic retrieval, embeddings/vector
search, ML/DL, LLM reasoning, persistence, authentication, UI, monitoring, or
autonomous behavior.
