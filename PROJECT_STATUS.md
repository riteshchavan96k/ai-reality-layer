# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 38 — Reality Retrieval Engine — implementation and validation coverage complete.

### Step 38 Scope

- A pluggable retrieval-provider interface executes the Step 37 retrieval contract.
- Required retrieval requests are sent to the configured provider.
- Static tasks explicitly skip external retrieval.
- Provider output is normalized into a stable retrieval result shape.
- An unconfigured provider reports `provider_unavailable` instead of fabricating external information.
- Required retrieval is a prerequisite for model execution when the retrieval engine is invoked by orchestration.
- The retrieval engine can be injected into orchestration for real providers and deterministic tests.
- Existing execution, evaluation, recovery, budget, approval, trace, and outcome-memory behavior remains intact.

### Step 38 Design Boundary

This step introduces retrieval execution through a provider abstraction, but the default runtime has no external provider configured and therefore never fabricates web or world information. It does not implement web search, a production external provider, RAG, evidence ranking, source verification, factual correctness, or ML training. Those capabilities can be added as providers and downstream grounding layers without changing the retrieval contract.
