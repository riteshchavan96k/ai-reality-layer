# Step 179 — Canonical Completed Evidence Reality-State Integration

## Objective

Make the canonical completed-retrieval path produce a coherent claims/evidence/provenance/freshness/confidence Reality State end to end, and validate the existing opt-in HTTP retrieval configuration as an actual MVP path.

## Why this is the correct next step

Step 178 restored a green repository baseline and repaired several integration defects.

With the suite green, the next priority is product-path correctness rather than another defensive micro-contract.

The current evidence normalizer emits:

`status="completed"`

for successful retrieved evidence.

Claim extraction and grounding already recognize that canonical status.

However, two downstream Reality Layer components still required the older compatibility alias:

`status="usable"`

- `ClaimEvidenceLinker`;
- `SourceProvenanceBuilder`.

The consequence was serious for the MVP path:

```
completed retrieval
→ usable evidence quality
→ extracted claims
→ claim linking unavailable
→ provenance unavailable
→ freshness unavailable
→ degraded Reality State
```

There was also a trust inconsistency in confidence aggregation: source freshness could contain one or more `unknown` assessments while the aggregate state was still labelled `supported`.

Step 179 repairs those boundaries and proves the complete configured retrieval → Reality State path.

## Canonical completed-evidence semantics

The canonical current evidence status remains:

`completed`.

Step 179 does not rename it to `usable`.

Instead, downstream consumers that semantically operate on usable completed evidence now accept:

- `completed` as the canonical status;
- `usable` as a legacy compatibility alias.

This preserves later canonical terminology without unnecessarily breaking older direct callers.

## Claim-evidence linking

`ClaimEvidenceLinker` now links extracted claims when evidence status is either:

- `completed`;
- `usable`.

For canonical completed evidence with valid URI-bearing sources, extracted claim source references therefore become explicit `ClaimEvidenceLink` records.

This restores the product's core:

`claim → evidence source`

traceability on the normal retrieval path.

## Source provenance

`SourceProvenanceBuilder` now accepts canonical completed evidence as well as the legacy usable alias.

Successful evidence can therefore reach:

- stable SHA-256 source identity;
- source reference;
- URI;
- source title;
- observation metadata;
- freshness assessment.

This closes the provenance/freshness break caused by the stale status gate.

## Unknown freshness is uncertainty

`SourceFreshnessEvaluator` intentionally returns an `unknown` assessment when no explicit freshness window is declared.

Before Step 179, `RealityConfidenceSignalAggregator` emitted the signal:

`freshness_uncertain`

but could still return:

`status="supported"`.

Step 179 makes the aggregate status consistent with its own signal:

- unknown freshness → `uncertain`;
- stale freshness → `uncertain`;
- missing freshness → `uncertain`;
- fully linked evidence + usable known-fresh sources + no conflicts may remain `supported`.

This is intentionally conservative. The system does not treat “retrieved just now” as proof that the underlying published information is fresh unless the configured freshness contract establishes that.

## End-to-end Reality State

Step 179 adds an integration regression that injects a canonical completed retrieval result and validates the complete deterministic chain:

```
retrieval completed
→ evidence completed
→ evidence quality usable
→ claims usable
→ claim/evidence links usable
→ source provenance usable
→ source observation usable
→ freshness usable but unknown
→ confidence uncertain
→ Reality State uncertain
```

The state is `uncertain`, not `supported`, because the test intentionally provides no declared freshness window.

That distinction is a core Reality Layer trust behavior.

## Reality State state-initialization repair

The first Step 179 end-to-end regression uncovered a separate active-path defect in `OrchestrationPipeline.build_reality_state()`.

The method attempted to assign:

`state.retrieval_contract = ...`

but `OrchestrationState.retrieval_contract` is a read-only derived property backed by:

`state.analysis["reality_retrieval"]`.

That made the public Reality State path fail before retrieval execution.

Step 179 now builds the retrieval contract into a local value and initializes `state.analysis` with that canonical contract before entering `_retrieve_and_ground()`.

This preserves the existing state model rather than adding a setter solely to accommodate an incorrect write.

## Existing HTTP retrieval path

The repository already contains an opt-in `HttpRetrievalProvider` and default composition support through:

`ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE`.

Step 179 does not introduce a vendor-specific search integration or credential.

Instead, it validates that configured generic HTTPS retrieval can now flow through the complete Reality State pipeline.

The dedicated regression configures the environment, replaces network I/O with a deterministic fake HTTPS response, and proves that the normal default dependency graph returns claims, links, provenance, observation, freshness, and confidence.

## Developer configuration

The README now documents the minimum configuration:

```bash
export ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE='https://retrieval.example.com/search?q={query}'
```

The configured endpoint must use HTTPS and include the literal `{query}` placeholder.

A successful provider response is a JSON object such as:

```json
{
  "status": "completed",
  "content": "Company X launched Feature A today.",
  "sources": [
    {
      "title": "Official Company X update",
      "uri": "https://example.com/company-x"
    }
  ]
}
```

The Reality Layer remains provider-neutral: the configured service is responsible only for retrieval; claims/provenance/freshness/conflict/confidence/Reality State assembly remains inside this project.

## Compatibility

Step 179 preserves:

- legacy evidence status `usable` for direct component callers;
- existing retrieval provider contracts;
- existing HTTP retrieval environment variable;
- existing Reality State API response schema;
- deterministic claim extraction;
- deterministic provenance/freshness/conflict/confidence methods.

No external credential is introduced.

## Safety invariant

canonical completed retrieval
→ usable evidence quality
→ claims
→ explicit claim/evidence links
→ stable source provenance
→ source observation
→ freshness assessment
→ conservative confidence
→ Reality State.

A linked/provenance-backed Reality State is still not a guarantee that source content is true. Unknown freshness now remains explicit uncertainty rather than being promoted to support.

## Design boundary

Step 179 repairs the existing MVP retrieval-to-Reality-State path.

It does not add:

- a vendor-specific search API;
- credentials;
- vector databases;
- embeddings;
- model training;
- semantic claim verification;
- learned confidence calibration;
- autonomous agents;
- deployment infrastructure.

## Regression coverage

`backend/tests/test_step179.py` covers:

1. canonical completed evidence claim linking;
2. legacy usable evidence linking compatibility;
3. canonical completed evidence provenance;
4. legacy usable provenance compatibility;
5. unknown freshness forcing uncertain confidence;
6. fully linked known-fresh evidence remaining supported;
7. end-to-end completed retrieval producing claims, links, provenance, observation, freshness, and Reality State;
8. opt-in configured HTTP retrieval reaching the same Reality State pipeline without real network access.

## Validation truth

Step 179 reached a real GitHub-hosted green full-repository result.

Backend tests run #72 (`37118462174`) on commit `b0abd70aa5caa4260c68e3db7bd79735706d07af` completed successfully with:

- checkout: passed;
- Python 3.13 setup: passed;
- dependency installation: passed;
- backend compile validation: passed;
- complete pytest suite: **1183 passed**;
- failures: **0**;
- Step 179 regression tests: passed.

The run includes the canonical completed-evidence linking/provenance repairs, unknown-freshness uncertainty behavior, the end-to-end completed-retrieval Reality State regression, the configured generic HTTPS retrieval regression, and the Reality State state-initialization repair.

The final project-status synchronization is validated by a separate GitHub Actions run before Step 179 receives its completion checkmark.
