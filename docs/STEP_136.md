# Step 136 — Retrieval Provider Request Context Hardening

## Objective

Preserve the retrieval freshness requirement when a RetrievalRequest crosses the provider-neutral execution boundary.

Step 129 introduced freshness_max_age_seconds on the retrieval request, but the provider-facing RetrievalProviderRequest did not carry that field. Step 136 closes that contract gap so external providers receive the complete retrieval request context.

## Implementation

- Extended RetrievalProviderRequest with optional freshness_max_age_seconds.
- Added the same positive-number validation used by the canonical retrieval request.
- Preserved the field through from_mapping() and to_dict().
- Omitted the field when it is unspecified, preserving existing serialized request shape for callers that do not declare freshness.
- Fixed the production dependency module's missing os import required by the Step 135 opt-in environment configuration.
- Added dedicated regression coverage for round-trip preservation, validation, backward-compatible omission, and construction of the configured external provider dependency.

## Pipeline Boundary

Source Plan → RetrievalRequest → RetrievalProviderRequest → Provider Execution → Retrieval Result

The freshness requirement remains declarative. This step does not claim that an external provider can prove source freshness; Step 129's freshness evaluator remains responsible for evaluating observation age.

## Safety and Scope

This step does not add credentials or secrets, a hardcoded vendor, network calls in tests, LLM/RAG/embeddings/vector search, semantic truth verification, or ML/DL training or inference.

## Validation Truth

Dedicated Step 136 regression tests are committed, but local pytest execution has not been performed in this session. GitHub status checks are not configured, so no automated test-pass claim is made.