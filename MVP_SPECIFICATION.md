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
semantic claim extraction remains future work. Step 207 adds an optional
provider-neutral structuring execution boundary with a fail-closed default;
no semantic model is configured or automatically invoked.
Current implementation note: Step 208 ensures submitted multi-document evidence
performs global claim deduplication before optional structuring, preserving
structured metadata and all supporting source references.
Current implementation note: Step 209 validates normalized semantic
structuring-method identity and bounds adapter-provided method/reason
metadata to prevent contradictory or oversized canonical claims.
Current implementation note: Step 210 caps **optional semantic adapter input**
at 10,000 claim-text characters; longer claims remain fully attributed and
unstructured without calling the adapter. The default no-model path is unchanged.
Current implementation note: Step 211 closes the optional-semantic-adapter
claim-count budget bypass for lower-level `usable` evidence. With an injected
adapter, at most 2,000 unique claims can proceed to optional structuring;
legacy `usable` extraction without an adapter remains backward compatible.

### Evidence

Current implementation note: Step 215 requires canonical claim–evidence
link source references to be trimmed and rejects repeated case-insensitive
claim/source pairs in typed and mapping-shaped link results. A claim may
still have multiple genuine distinct source references; no new claims or
independent source authenticity are inferred from this structure.


Information supporting or challenging a claim.

### Source

Origin of the evidence.

Current implementation note: Step 212 uses consistently trimmed source-URI
identities for retrieval evidence, extracted claims, provenance hashing,
evidence links, and observation matching. Whitespace-alias duplicates are
rejected rather than counted as separate evidence sources. This does not
certify publisher authenticity or factual correctness.

### Provenance

The relationship between claim, evidence, and source.

Current implementation note: Step 213 requires canonical source-provenance
records to use the exact same trimmed `source_ref` and `uri`, and
requires unique source IDs and references within a provenance result.
This prevents contradictory identities in directly supplied canonical
contracts but does not authenticate publishers or prove source claims.

### Freshness

Current implementation note: Step 214 requires one observation and
one freshness assessment per source ID **within each Reality State result**.
Direct and mapping-shaped temporal contracts reject duplicated source IDs,
preventing the same source from inflating fresh/stale/unknown counts. This
is not a temporal history store and does not authenticate source contents.


Information about how current the evidence is.

### Conflict

A disagreement between claims or evidence.

Current implementation note: Step 216 requires canonical conflict records
to use trimmed source references and prevents repeated unordered,
case-insensitive claim pairs in direct and mapping-shaped results. This
keeps candidate conflict counts from being inflated. The detector remains
restricted to explicit deterministic negation, not semantic contradiction
verification.

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

Current evaluation note (Step 217): a fixed 48-case controlled synthetic
Reality State quality dataset and separate runner now measure text/source
attribution, candidate-conflict detection, false structural support, and
safe abstention. The oracle facts and URLs are explicitly **simulated**;
results cannot substantiate external factual accuracy, publisher
credibility, generalization, or production readiness. The full suite
continues to measure software correctness separately. See
`docs/STEP_217.md` and `docs/STEP_217_BASELINE.md`.

Current evaluation note (Step 218): the offline quality evaluation now
also uses eight real official publisher historical-release pages as
manual reference anchors for 48 scenarios. Summaries are original
reviewer-authored paraphrases, NOT immutable original page captures;
several scenarios intentionally change content, introduce synthetic
conflicts, or use an unrelated genuine official URL. Confidence and
source-relevance failures are visible in the committed scorecard.
This does not constitute field accuracy or independent source-content
authentication. See `docs/STEP_218.md`.

Current implementation note (Step 219): an explicitly provided `entity`
now activates a conservative whole-identifier match for every linked
claim before Reality State can be marked `supported`. Missing textual
alignment downgrades to `uncertain`, preserving original freshness,
conflict and link counts. The check does not verify publisher content,
semantic entailment or independent factual truth; a forged claim that
mentions the entity can still pass. Callers with no explicit entity
retain legacy behavior. The historical Step 218 scorecard is preserved,
with a separate Step 219 post-gate scorecard in
`docs/STEP_219_SCORECARD.md`.


Step 220 opt-in assurance note: direct developer-submitted evidence
may require `require_independent_source_text_match=true`, which fails
closed unless each submitted excerpt appears verbatim in a canonical
source URI's text independently returned by a server-installed reader.
The check records auditable per-source results inside the existing
evidence mapping and never accepts client-controlled verification
assertions. No reader is configured by default: strict-mode requests
remain `uncertain` until the operator installs a safely implemented
provider. A match is not publisher authentication or factual proof.
The Step 220 simulated-observer scores cannot establish real-world
source assurance; see `docs/STEP_220.md`.


Step 221 source-observer note: a server operator can now enable genuine
HTTPS page retrieval for strict evidence checks via exact-URL JSON
allowlist in `ARL_INDEPENDENT_SOURCE_ALLOWED_URLS`. By default it is
disabled. The reader validates global DNS destinations and pins the
TLS connection to a checked address, rejects redirects and oversized
or unsupported responses, and returns SHA256 of original captured
response bytes and UTC observation time for auditable matched sources.
It does **not** establish publisher signature/authorship, truth or
semantic relevance, and raw source pages are not durably archived.
Network behavior is tested offline with fake transports; real site
acceptance testing is still needed. See `docs/STEP_221.md`.

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