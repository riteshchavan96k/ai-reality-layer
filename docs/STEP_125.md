# Step 125 — Evidence Claim Extraction Boundary

## Objective

Establish the first explicit claim-extraction boundary after evidence normalization and quality validation.

## Repository-derived architectural boundary

Retrieval → Retrieval Result Consumption → Evidence Normalization → Evidence Quality Validation → Claim Extraction → Grounding Context → Execution Authorization → Model Execution.

Step 125 introduces claim candidates without pretending that deterministic sentence splitting is semantic verification.

## Implementation

Step 125 adds:

- EvidenceClaim, an immutable candidate-claim contract;
- ClaimExtractionResult, an immutable extraction result contract;
- EvidenceClaimExtractor, a deterministic baseline extractor;
- source URI preservation on extracted candidates when evidence provides URIs;
- duplicate candidate removal using case-insensitive normalized text;
- explicit usable, empty, and unavailable extraction states;
- deterministic serialization through to_dict(); and
- fail-closed validation for malformed evidence and invalid result states.

## Pipeline integration

After evidence quality validation, OrchestrationPipeline._retrieve_and_ground now invokes the injected EvidenceClaimExtractor.

The resulting canonical claim-extraction state is recorded in state.analysis[reality_claim_extraction] and included in the existing reality_retrieval analysis record.

Claim extraction does not block execution by itself in this step. Existing evidence-quality and grounding authorization gates remain authoritative.

## Provenance boundary

When evidence contains source URIs, those URIs are carried onto each candidate because the current retrieval content is an aggregated evidence payload. Step 125 does not claim that each individual sentence has been independently verified against a particular source.

This is intentionally a provenance-preserving candidate boundary, not a claim-evidence verification system.

## Deterministic baseline

The extractor currently separates non-empty evidence content into sentence-like units, normalizes whitespace, removes duplicate candidate text, and emits immutable claim candidates.

This is deliberately a baseline. It is not intended to replace later semantic claim extraction where model intelligence is justified.

## Failure behavior

The implementation rejects malformed evidence structures and invalid claim/result states deterministically.

Non-usable evidence produces an unavailable claim-extraction result rather than fabricated claims.

Usable evidence without extractable text produces an empty result.

## Scope discipline

This step introduces only the claim-extraction boundary required by the existing evidence-to-reality architecture.

It does not add LLM providers, RAG frameworks, embeddings, vector databases, external retrieval credentials, factual verification, conflict resolution, confidence scoring, or unrelated infrastructure.

## Validation

Dedicated Step 125 regression coverage verifies:

- immutable claim contracts;
- deterministic serialization;
- sentence candidate extraction;
- duplicate removal;
- source-reference preservation;
- non-usable evidence handling;
- empty evidence handling;
- malformed evidence rejection; and
- invalid result-state rejection.

GitHub status checks are not configured for this repository, so no CI test pass is claimed. Local pytest execution remains required on the development machine.