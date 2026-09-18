# Step 126 — Claim-to-Evidence Linking Boundary

## Objective

Establish an explicit provenance relationship between extracted candidate claims and the evidence sources already carried by the retrieval/evidence pipeline.

## Repository-derived architectural boundary

Retrieval → Retrieval Result Consumption → Evidence Normalization → Evidence Quality Validation → Claim Extraction → Claim-to-Evidence Linking → Grounding Context → Execution Authorization → Model Execution.

Step 126 makes the relationship explicit without treating the relationship as factual verification.

## Implementation

Step 126 adds:

- immutable ClaimEvidenceLink for a claim/source provenance relationship;
- immutable ClaimEvidenceLinkingResult as the canonical linking result;
- ClaimEvidenceLinker as the deterministic linking boundary;
- source-reference intersection against the actual evidence source URIs;
- duplicate claim/source-pair removal;
- explicit usable, empty, and unavailable linking states;
- deterministic serialization through to_dict(); and
- fail-closed validation for malformed claim/evidence structures.

## Provenance semantics

A link means that the claim's existing source reference matches a source URI actually present in the evidence payload. It does not mean the source has independently verified the claim, that the source contains the exact claim text, or that the claim is true.

The implementation deliberately does not create links from source titles, source order, URL similarity, semantic guesses, or unsupported inference. Unusable evidence also fails closed and produces an unavailable linking result.

## Pipeline integration

After Step 125 claim extraction, OrchestrationPipeline._retrieve_and_ground invokes the injected ClaimEvidenceLinker.

The canonical result is recorded in state.analysis[reality_claim_evidence_linking] and included in the existing reality_retrieval analysis record.

Linking does not block model execution by itself. Existing evidence-quality, grounding, and execution-authorization gates remain authoritative.

## Scope discipline

This step adds the missing claim-to-evidence provenance boundary only.

It does not add LLM providers, RAG frameworks, embeddings, vector databases, external retrieval credentials, factual verification, conflict resolution, confidence scoring, freshness evaluation, ML training, or unrelated infrastructure.

## Validation

Dedicated Step 126 regression coverage verifies:

- immutable link contracts;
- deterministic serialization;
- source-reference matching;
- rejection of invented/unknown links;
- duplicate link removal;
- unavailable and empty handling;
- dictionary compatibility; and
- invalid result-state rejection.

GitHub status checks are not configured for this repository, so no CI test pass is claimed. Local pytest execution remains required on the development machine.