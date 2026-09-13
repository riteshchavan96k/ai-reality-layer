# Step 79 — Retrieval Provider Selection Policy Contract

## Objective

Establish a dedicated policy boundary for the final decision that a retrieval provider is eligible after the existing availability, health, and capability gates have been evaluated.

## Implementation

- Added `RetrievalProviderSelectionPolicy` as the policy protocol.
- Added `DefaultRetrievalProviderSelectionPolicy` as the deterministic default implementation.
- The default policy requires availability and health evaluation results to be supported.
- Capability evaluation is required only when capability metadata exists, preserving backward compatibility for legacy providers without descriptors.
- Invalid policy inputs are rejected deterministically.
- Updated `RegistryRetrievalProviderSelector` to inject and consult the selection policy after existing gate-specific short-circuit checks.
- Policy rejection produces the stable reason `retrieval_provider_selection_policy_rejected`.
- Added dedicated Step 79 regression coverage for policy behavior, invalid inputs, backward compatibility, and selector integration.

## Design Boundary

This step separates combined provider-selection policy from individual availability, health, and capability evaluation mechanisms. It does not add external providers, active health probes, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

## Selection Model

The current selection path remains:

`provider lookup → availability evaluation → health evaluation → capability evaluation → selection policy → provider selection`

Existing gate-specific rejection semantics remain intact; the new policy is an additional final eligibility boundary and is injectable for future policy evolution.

## Validation Truth

Implementation, integration, regression tests, and documentation are complete. Local test execution is still pending, so no local test pass is claimed.
