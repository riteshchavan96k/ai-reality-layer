# AI Reality Layer — MVP Specification

## 1. MVP Objective

Build the smallest usable version of AI Reality Layer that tests whether AI developers benefit from structured, evidence-backed representations of changing real-world information.

## 2. Core Product

AI Reality Layer accepts a real-world research query or entity and produces a structured reality state containing claims, evidence, provenance, freshness, conflicts, and confidence.

## 3. Initial User

AI application developers and small AI teams building research, intelligence, or agentic applications.

## 4. Core User Problem

AI applications often consume search results, documents, or retrieved context without a structured representation of which claims are current, supported, conflicting, or trustworthy.

## 5. MVP Input

The MVP accepts:

- an entity
- a research question

Example:

"What is the current status of Company X?"

## 6. MVP Pipeline

Input
→ Query understanding
→ Information retrieval
→ Source collection
→ Claim extraction
→ Evidence linking
→ Provenance tracking
→ Freshness analysis
→ Conflict detection
→ Confidence assessment
→ Reality State
→ Structured API response

## 7. Core Objects

### Entity

A real-world object being investigated.

Current implementation note: Step 204 adds a first-class canonical entity slot
to every Reality State and optional explicit entity input to both Reality State
APIs. Automatic entity extraction/resolution remains future work.

### Claim

A statement about an entity.

Current implementation note: Step 206 adds a canonical claim semantic-structure
slot with validated `structured` subject/predicate/object and explicit
`unstructured` states. The current deterministic sentence extractor does not
attempt semantic structuring and therefore emits `unstructured`; automatic
semantic claim extraction remains future work.

### Evidence

Information supporting or challenging a claim.

### Source

Origin of the evidence.

### Provenance

The relationship between claim, evidence, and source.

### Freshness

Information about how current the evidence is.

### Conflict

A disagreement between claims or evidence.

### Confidence

An assessment of how strongly available evidence supports a claim.

### Reality State

A structured representation of the current evidence-supported state of an entity or question.

## 8. MVP Output

The system should return structured machine-readable data containing:

- entity
- claims
- evidence
- sources
- provenance
- timestamps
- freshness
- conflicts
- confidence
- last verification time

Current implementation note: Step 205 exposes this as
`verification.verified_at`, meaning the UTC time when deterministic Reality
State signal-snapshot assembly completed. It is not a publication timestamp,
event timestamp, or certificate of factual truth.

## 9. MVP Features

1. Query input
2. Information retrieval
3. Source collection
4. Claim extraction
5. Evidence linking
6. Source provenance
7. Timestamp tracking
8. Basic freshness analysis
9. Basic conflict detection
10. Basic confidence assessment
11. Structured JSON output
12. API endpoint

## 10. Explicitly Out of Scope for V1

- AGI
- custom foundation model
- training a large model
- hundreds of model integrations
- massive enterprise integrations
- industry-specific deployments
- continuous global monitoring
- advanced autonomous agents
- complex enterprise dashboard
- guaranteed factual truth

## 11. Product Differentiation Hypothesis

AI Reality Layer is intended to operate above raw retrieval and below AI application reasoning by converting information into structured, evidence-backed reality states.

## 12. Success Criteria

The MVP should demonstrate that:

1. Claims can be generated from retrieved information.
2. Claims can be connected to evidence.
3. Evidence can be traced to sources.
4. Freshness can be represented.
5. Obvious conflicts can be detected.
6. Confidence can be represented.
7. The output can be consumed programmatically.
8. Developers find the structured reality state useful.

## 13. Core Product Hypothesis

Developers will find structured, evidence-backed reality states more useful for building reliable AI applications than directly consuming raw search or RAG results.

## 14. Long-Term Direction

Potential future capabilities:

- persistent reality states
- entity resolution
- temporal knowledge
- continuous updates
- event detection
- multi-model routing
- knowledge graphs
- enterprise data connectors
- industry-specific reality layers

These are not part of V1.

## 15. Status

MVP specification defined.

Technical architecture is the next stage.