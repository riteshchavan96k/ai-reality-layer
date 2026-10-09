# Step 215 — Canonical Claim–Evidence Link Identity Integrity

## Identified defect in the completed Step 214 repository

Step 212 established consistent canonical (whitespace-trimmed) source URI
identity across retrieved evidence, extracted claims, and provenance.
Step 213 made source provenance IDs and references unique within a result.
Step 214 enforced unique source IDs within observation and freshness
assessments.

The existing production `ClaimEvidenceLinker` also already removes
duplicate `(claim.text.casefold(), source_ref)` pairs when building its
result.

However, the *canonical* `ClaimEvidenceLink` and
`ClaimEvidenceLinkingResult` contracts still accepted inconsistent
records on direct construction or mapping deserialization:

1. A link with `source_ref=" https://example.test/a "` was accepted
   even though provenance records now require the exact trimmed identity.
2. The same claim/source pair could appear multiple times in a canonical
   result. Since `linked_claim_count` counts **distinct claim text**,
   this duplication did not violate the existing counter invariant,
   yet `link_count` could overstate the number of relationships. Different
   letter case or `linking_method` values could also bypass plain
   dataclass-equality-based deduplication.

These are real contract integrity issues at a boundary already consumed by
Reality State and confidence reporting. This step does not add an invented
AI feature.

## Scope and objective

Ensure the existing canonical claim–evidence link records uphold the same
source reference and relationship identity rules as the production linker.

The objective is to **reject**, not silently coalesce, malformed canonical
results. Upstream source-scoped evidence, claim deduplication, and the
production linker's own deduplication remain unchanged.

## Minimal code changes

Only `backend/app/reality/claim_evidence_linking.py` application logic is
changed.

### Canonical single-link source identity

After the pre-existing nonempty `source_ref` check,
`ClaimEvidenceLink.__post_init__` now requires:

`source_ref == source_ref.strip()`

A padded URI/ref raises a `ValueError`. No URL casing, slashes, query
parameters, percent escapes, redirects, or hostname rules are changed.
This enforces the Step-212 canonical identity rather than inventing a
new notion of URL equivalence.

### Unique claim/source relationships

`ClaimEvidenceLinkingResult.__post_init__` now checks:

```python
link_keys = {(link.claim_text.casefold(), link.source_ref) for link in self.links}
if len(link_keys) != len(self.links):
    raise ValueError("claim-evidence links must have unique claim-source pairs")
```

The key matches the existing production `ClaimEvidenceLinker`
algorithm: a claim's text is compared case-insensitively, but a
source's canonical URI/ref is kept exact. `linking_method` is metadata,
not a separate supporting source relationship.

**Valid cases remain valid:**

- A single claim linked to source A and source B (two different pairs);
- Two different claims linked to source A;
- Two source URIs differing meaningfully (e.g. trailing slash);
- Empty or unavailable linking states with zero links;
- The existing deterministic source-scoped and submitted-evidence
  pipelines, including their current linked-claim counts.

### Mapping inputs

Existing `ClaimEvidenceLinkingResult.validate(mapping)` builds typed
`ClaimEvidenceLink` instances, then a typed
`ClaimEvidenceLinkingResult`. Its normalizer uses the same validation.
Thus the new checks also reject padded or repeated pairs from
mapping-shaped callers without a new validator/service.

## Tests and acceptance requirements

`backend/tests/test_step215.py` covers:

- Padded direct source refs, including tabs and newlines, rejected;
- Padded mapping-shaped refs rejected by validator and normalizer;
- Duplicate exact pairs, case-insensitive claim aliases, and pairs with
  different `linking_method` rejected;
- Explicit typed constructors and both mapping/typed nested inputs;
- Legitimate multi-source support for a single candidate claim retained;
- Multiple separate claims supported by one source retained;
- The production linker's own deduplication and source normalization;
- Low-level link references agreeing with canonical provenance refs;
- Empty and unavailable historical linking behavior unchanged;
- A real developer-submitted two-source Reality State containing exactly
  two distinct links to one claim, with stable source hashes.

The full Python 3.13 GitHub-hosted backend compilation and pytest suite,
including all existing Step 197–214 regressions, must pass.

## Honest safety and compatibility boundaries

This is **relationship identity integrity**, not semantic entailment,
publisher authentication, factual truth checking, calibrated confidence,
or proof that the listed sources are independent.

The new invariant does not introduce a new model, ML/DL/Hugging Face/LLM
integration, external service, database, API field, graph engine, or
change to any existing source and claim extraction budgets.

It also does not guarantee that independently supplied canonical
link pairs are backed by an actual external source: the production
linker already intersects claim source refs with evidence sources.
That issue must not be falsely portrayed as solved by this step.

## Completion requirements

Mark Step 215 complete only after full GitHub-hosted backend compile and
pytest pass on feature-branch head, the pull request is merged into `main`,
the merged implementation independently passes the full workflow, and
the final status synchronization commit passes the same workflow on its
exact `main` SHA.
