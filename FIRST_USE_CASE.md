# AI Reality Layer — First User & Use Case

## 1. Initial ICP

Developers and small AI teams building AI research, intelligence, or agentic applications that depend on changing information from multiple sources.

This is an initial ICP hypothesis and may change after user validation.

## 2. Initial User

Primary user:

AI application developer / AI agent developer.

## 3. Problem

AI applications often retrieve information as disconnected documents or search results.

This makes it difficult to determine:

- which information is current
- which claims are supported
- where information came from
- whether sources conflict
- how confident the system should be
- when information was last verified

## 4. Initial Use Case

Provide AI agents with structured, evidence-backed information about real-world entities and claims.

The system should potentially include:

- claims
- evidence
- source provenance
- timestamps
- freshness
- conflicts
- confidence

## 5. Example

User asks:

"What is the current status of Company X?"

Traditional flow:

User
→ AI agent
→ Search/RAG
→ Documents
→ LLM
→ Answer

AI Reality Layer hypothesis:

User
→ AI agent
→ AI Reality Layer
→ Evidence collection
→ Claim extraction
→ Source verification
→ Freshness checking
→ Conflict detection
→ Confidence assessment
→ Structured reality state
→ AI agent
→ Answer

## 6. Why This User

AI developers are relatively accessible for an early zero-budget startup.

They also represent a technically relevant user group for testing an infrastructure/API product.

## 7. Long-Term Expansion

Potential future markets include:

- enterprise AI
- business intelligence
- procurement
- research
- customer support
- financial intelligence
- supply-chain intelligence
- other industry-specific AI systems

These are future possibilities, not initial MVP commitments.

## 8. Initial Product Hypothesis

AI Reality Layer could eventually expose an API that allows AI applications to request evidence-backed reality states rather than directly consuming unstructured search results.

## 9. Key Risk

Existing technologies already provide search, retrieval, RAG, grounding, evaluation, observability, and agent infrastructure.

Therefore the product must demonstrate a meaningful advantage in representing:

- claims
- evidence
- provenance
- freshness
- conflicts
- confidence

## 10. Validation Requirement

Before investing heavily in development, we need to test whether developers actually experience this problem and whether our proposed solution is valuable enough to use.

## 11. Current Decision

Initial ICP:

AI application and agent developers.

Initial use case:

Evidence-backed, current reality states for AI applications.

Status:

Hypothesis selected — user validation still required.