# Step 128 — Source Observation Metadata Boundary

## Objective

Record when each identified evidence source was observed by the retrieval pipeline, creating the temporal metadata required for later freshness evaluation without prematurely declaring a source fresh or stale.

## Architecture

Retrieval → Evidence Normalization → Evidence Quality Validation → Claim Extraction → Claim-to-Evidence Linking → Source Provenance Identity → Source Observation Metadata → Grounding Context → Execution Authorization → Model Execution.

## Implementation

Step 128 adds:

- immutable SourceObservation records;
- immutable SourceObservationResult;
- SourceObservationBuilder with an injectable clock;
- timezone-aware ISO-8601 observation timestamps;
- one observation record per stable source identity;
- fail-closed propagation from unavailable/empty provenance; and
- deterministic serialization.

The observation timestamp represents when the system observed the source during retrieval processing. It is not a publication timestamp, modification timestamp, freshness score, or truth assessment.

## Scope discipline

This step deliberately does not infer freshness from URL patterns, titles, source age, or content. It does not claim that a source is current merely because it was recently retrieved.

It does not add freshness thresholds, external retrieval, network access, credentials, conflict detection, confidence scoring, factual verification, RAG, embeddings, vector databases, ML training, or LLM integration.

## Validation

Dedicated Step 128 regression coverage verifies immutability, deterministic clock injection, one-to-one source observations, fail-closed states, timezone requirements, future timestamp rejection, and invalid result-state handling.

GitHub status checks are not configured. No CI or local pytest pass is claimed unless an actual test run reports it.
