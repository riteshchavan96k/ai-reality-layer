# Step 155 — Claim-Evidence Linking Contract Validation

## Objective

Harden the next existing downstream Reality Layer boundary after Step 154: the result produced by claim-to-evidence linking.

## Why This Is the Correct Next Boundary

The orchestration pipeline already performs claim extraction and then creates `ClaimEvidenceLinkingResult` before conflict detection, provenance construction, freshness evaluation, confidence aggregation, and Reality State assembly.

Step 154 established the canonical validation boundary for claim extraction. Step 155 therefore applies the same contract-hardening pattern to the immediately downstream claim-evidence linking result.

## Scope

Step 155 validates:

- result status;
- link collection shape;
- nested `ClaimEvidenceLink` fields;
- claim count;
- linked claim count;
- source count;
- linking execution state;
- unavailable-result reasons;
- consistency between status and links.

A dedicated `ClaimEvidenceLinkingResultNormalizer` accepts either the canonical result or a compatible mapping and routes mapping-shaped results through the canonical validator.

## Safety Invariant

retrieval result
→ retrieval-result validation
→ retrieval consumption validation
→ evidence normalization
→ evidence-normalization validation
→ evidence normalization consumption validation
→ evidence quality validation
→ claim extraction validation
→ claim-evidence linking validation
→ downstream conflict/provenance/freshness/confidence processing

## Product Scope Discipline

No new retrieval provider, network behavior, LLM, RAG system, embedding model, vector database, ML/DL model, or semantic truth claim is introduced by this step.

The existing deterministic claim-evidence linking behavior remains unchanged. This step concerns contract validation only.

## Validation Truth

Dedicated Step 155 regression tests are committed. Local pytest execution remains required before claiming a full repository test pass. GitHub status checks are not configured.

## Repository Write Note

The canonical normalizer and Step 155 regression coverage are committed. The existing `claim_evidence_linking.py` file already enforces the result invariants in its constructor; the new normalizer uses that existing canonical result contract. A direct in-place rewrite of the existing file was not applied because the repository write interface returned a blob-SHA conflict despite repeated fresh reads; no destructive replacement was attempted.
