# Step 187 — Source-Scoped Submitted-Evidence Round-Trip Integrity

## MVP basis, verification and identification

The AI Reality Layer MVP promises evidence-backed claim provenance: a
developer must be able to trace a claim back to **the exact source's
text**, not merely to a URI appearing alongside a combined document body.

This milestone follows verified behavior on `main` after Steps 180–186:

- Step 180 accepts multiple source-scoped developer documents, and
  `SubmittedEvidenceBundle.extract_claims()` correctly processes each
  original document and merges only equal claim texts across sources.
- Step 182 fixed the corresponding *configured retrieval* path to include
  `sources[].content`, preserving which original source supplied a claim.
  Its generic extractor deliberately rejects ambiguous multi-source
  combined content without per-source attribution.
- Before Step 187, `SubmittedEvidenceBundle.to_evidence()` **discarded
  per-source content**, emitting only `sources[].uri`/`title` plus an
  aggregate `content`. The returned Reality State could carry accurate
  claims produced by a separate bundle extraction method, but the
  `evidence` field alone could *not* reproduce those claims: generic
  re-extraction returned `ambiguous_source_attribution` for multi-source
  bodies. Clients also could not inspect the exact text tied to each URI.
- Step 184 bounds configured retrieval source size and claim count.
  Step 185 bounds the direct-submission global claim count to 2,000.
  Step 186 handles finite/strict freshness policies on both paths.

No preassigned per-step Step 187 title exists in the broad MVP roadmap.
This step closes the concrete evidence auditability/parity gap already
demonstrated in code, not an invented extra provider or AI capability.

## Implemented behavior

`SubmittedEvidenceDocument.source_dict()` now retains the **trimmed
original document text** in `content` alongside `uri` and `title`.
The bundle's existing `to_evidence()` already calls
`source_dict()`, so its canonical evidence envelope now contains:

```json
{
  "status": "completed",
  "sources": [
    {
      "uri": "https://example.test/a",
      "title": "First report",
      "content": "Shared claim. Only A."
    },
    {
      "uri": "https://example.test/b",
      "title": "Second report",
      "content": "Shared claim. Only B."
    }
  ],
  "content": "Shared claim. Only A.\n\nShared claim. Only B.",
  "source_count": 2,
  "has_content": true,
  "normalization_executed": true
}
```

The aggregate is exactly the deterministic `"\n\n"` concatenation of
trimmed per-source content, so the existing Step 182 extractor and
provider-neutral evidence normalizer can independently consume it.

For any **in-budget** submitted evidence bundle, the following property
now holds (including duplicate claims, negations, whitespace, newlines
and original URI ordering):

```python
bundle = SubmittedEvidenceBundle.from_mappings(documents)
state = build_reality_state_from_evidence(task, documents)
assert (
    EvidenceClaimExtractor().extract_result(state["evidence"]).to_dict()
    == state["claims"]
)
```

This equivalence applies to normal in-budget results (not over-limit
failure reasons: direct submission intentionally reports
`submitted_claim_limit_exceeded`, whereas the generic completed/retrieval
extractor reports `retrieved_claim_limit_exceeded`). Over-limit
developer evidence continues to produce **no partial claim graph**.

## Source observation trust and compatibility

- The raw `observed_at` from a developer remains separate from
  `sources[].content`: an independently typed
  `source_observation` record retains the explicit observation method
  `submitted_evidence_observation`, or
  `submitted_evidence_ingestion` for missing timestamps.
- No external URI is fetched or publisher authenticity verified.
- Exact same URI identifiers and provenance hashes, case-insensitive
  duplicate merging, 2,000-claim budget, freshness and conflict analysis,
  and both original HTTP API routes remain unchanged.
- Response shape is deliberately enriched: `sources[].content`
  duplicates text already present in top-level `content`. A full
  submission is capped at 20 sources × 50,000 characters, but clients
  should account for this expected duplicated output size. This is not
  an optional redaction or private-text filtering feature.
- The returned content is always developer-supplied evidence and must not
  be mistaken for an independent source verification. It may contain
  untrusted text/prompt injections and should be treated as data.

## Files changed and acceptance criteria

- `backend/app/reality/submitted_evidence.py`: keep original
  source-scoped document text in the canonical source mapping; do not
  attach misleading ingestion or reported time as publisher metadata.
- `backend/tests/test_step187.py`: verify source mapping, deterministic
  aggregation, exact claim round trips from returned evidence, duplicate
  source URI lineage, explicit/ingestion observation method preservation,
  conflict consistency, provider-neutral normalizer compatibility,
  serialized JSON/Pydantic/HTTP response structure, exact claim cap and
  fail-closed overflow, per-source input bounds and invalid URI rejection.
- `README.md` and `PROJECT_STATUS.md`: developer contract and actual
  verified completion status.

A successful Step 187 requires the *entire* existing backend regression
suite to pass after the feature PR merge and after the final
status-synchronizing `main` commit. Do not claim completion on PR
tests alone.

## Deliberate non-goals

No new API endpoint, model inference, LLM-generated assertions, source
fetching, publisher validation, claim truth calibration, date-of-publication
claims, persistence, authentication, deployment, or agent autonomy. The
core deliverable is auditable per-source **structural** evidence lineage.
