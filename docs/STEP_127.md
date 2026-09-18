# Step 127 — Source Provenance Identity Boundary

## Objective

Give each usable evidence source a stable, deterministic identity while preserving the exact source URI used by the existing claim-to-evidence provenance boundary.

## Architecture

Retrieval → Evidence Normalization → Evidence Quality Validation → Claim Extraction → Claim-to-Evidence Linking → Source Provenance Identity → Grounding Context → Execution Authorization → Model Execution.

## Implementation

Step 127 adds:

- immutable SourceProvenance records;
- immutable SourceProvenanceResult as the canonical result contract;
- SourceProvenanceBuilder as the source-identity boundary;
- deterministic SHA-256 identity derived from the exact URI;
- preservation of the original URI as both source_ref and uri;
- title preservation without using titles as identity;
- exact duplicate source-reference removal;
- explicit usable, empty, and unavailable states; and
- deterministic serialization.

The source ID is an identity mechanism only. It does not establish that a source is trustworthy, that a claim is true, or that a source verifies a claim.

## Safety and scope

The builder fails closed for unusable evidence and rejects usable sources without a non-empty URI. URI strings are not canonicalized or rewritten, because changing URL representation could change source identity semantics.

This step does not add external retrieval providers, network access, credentials, freshness scoring, conflict detection, confidence scoring, factual verification, RAG, embeddings, vector databases, ML training, or LLM integration.

## Validation

Dedicated Step 127 regression coverage verifies immutable contracts, deterministic identities, exact URI preservation, duplicate handling, malformed input, fail-closed behavior, and invalid result states.

GitHub status checks are not configured for this repository. No CI or local pytest pass is claimed unless independently observed.
