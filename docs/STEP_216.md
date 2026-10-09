# Step 216 — Canonical Conflict Identity Integrity

## Identification from the verified Step 215 repository

Step 215 strengthened canonical claim–evidence relationship identities.
Review of the existing deterministic conflict detector and its canonical
result types revealed a parallel correctness gap with direct significance
for Reality State confidence signals.

The production `ClaimConflictDetector` already maintains a `seen` set
of unordered, case-insensitive claim text pairs, so it does not emit the
same *detected* conflict multiple times.

However, `ClaimConflictResult` accepted direct or mapping-shaped
`conflicts` containing the same pair twice, even if the claim order was
reversed, capitalization differed, or source attribution changed.
The existing `conflict_count == len(conflicts)` check could still pass
and allow a duplicate pair to inflate the count passed to
`RealityConfidenceSignalAggregator`.

`ClaimConflict` also accepted whitespace-padded `source_refs_a` and
`source_refs_b` although Steps 212–215 established trimmed source
references for canonical provenance and evidence links.

This is a verified existing integrity gap, not a newly invented product
subsystem or a claim of general semantic conflict understanding.

## Objective

Enforce the **same unordered conflict-pair identity** in the canonical
result contract as the production detector, and require canonical
source references in individual conflict records. Retain all existing
schemas, deterministic detection rules, and legacy empty/unavailable
result semantics.

## Exact code changes

Only `backend/app/reality/claim_conflict.py` changes in production.

1. `ClaimConflict.__post_init__` continues to validate that each
   source ref group is a tuple of nonempty strings; it additionally
   rejects any `ref != ref.strip()`. Empty ref tuples remain valid.
   No URL rewriting, canonical case folding of URIs, or fabricated
   source references are introduced.
2. `ClaimConflictResult.__post_init__` validates that the set of
   `tuple(sorted((claim_a.casefold(), claim_b.casefold())))` keys
   has the same size as the `conflicts` tuple. A repeated pair raises
   `ValueError("claim conflicts must have unique claim pairs")`.
   Source ref provenance and conflict method are metadata on a
   relationship, not new independent contradictions.

The check is orientation-insensitive: swapping A/B cannot evade it.
It is intentionally not semantic text normalization, since the
production detector's deduplication identity is casefold-based.

Both `ClaimConflictResult.validate(mapping)` and the existing
normalizer already reconstruct these typed contract values; therefore
direct, mapping, and normalized inputs share the invariant.

## Valid behaviors retained

- Two genuinely different conflict pairs remain two entries.
- One pair can cite multiple distinct supporting source references.
- Source URIs with materially different characters remain different
  references, including distinct trailing-slash paths.
- A single pair still leads to `status="usable"` and
  `conflict_count=1`.
- Zero-conflict, unavailable, nonexecuted, and historical no-ref
  behaviors remain unchanged.
- The production detector still checks **only explicit deterministic
  negation pairs**, such as `X` against `not X`; it is not a
  logical theorem prover, entailment model, or general contradiction
  classifier.

## Tests

`backend/tests/test_step216.py` covers:

- Padded source refs rejected for either side of a typed conflict.
- Mapping and normalizer rejection of padded refs.
- Duplicate exact, reversed, case-variant, and different-provenance
  conflict pairs rejected before incorrect counts become canonical.
- Direct result constructor, mapping deserialization, and normalizer
  behavior for typed and dict nested conflicts.
- Multiple *distinct* conflicts, stable source lineage, and round trips.
- Empty source refs and zero/unavailable result compatibility.
- Existing deterministic conflict detector output and deduplication.
- Count propagation to `RealityConfidenceSignalAggregator`, retaining
  explicit uncertainty when genuine candidate conflicts exist.
- Real developer-submitted evidence Reality State with an explicit
  negation pair, one candidate conflict, and correct source refs.

The full historical Python 3.13 backend compilation and pytest suite,
including Steps 196, 199 and 212–215, must pass.

## Scope and honesty

This step enforces **structural identity for candidate conflicts**. It
does not independently validate that a claimed contradiction is true,
that sources are authentic, or that evidence is independent. It does
not add AI/ML/Hugging Face/LLM integration, a network provider, semantic
verification, a new graph, a database, or any public API changes.

## Completion

Step 216 can be marked complete only after the complete GitHub-hosted
backend Python 3.13 compilation and regression suite passes on the
feature branch, the PR merges, the merged implementation passes
independently on main, and the final status update's exact main SHA
passes the same workflow.
