# Step 206 — Canonical Structured Claim Representation Foundation

## Objective

Establish the canonical semantic representation that future claim-structuring
components will target, while preserving the current deterministic sentence
extractor's honest limitations.

The MVP defines Claim as a statement about an entity and the architecture calls
for structured claim extraction. Through Step 205, an `EvidenceClaim` carried
only:

- free-form claim text;
- source references;
- extraction method.

That was enough for provenance/linking, but there was no machine-readable place
to represent claim semantics such as subject, predicate, and object.

## Quality decision

Step 206 does **not** attempt to derive semantic triples with brittle regexes or
simple string heuristics.

The current extractor is a deterministic sentence splitter. It has no reliable
general mechanism for determining:

- semantic subject;
- predicate/relation;
- object/value;
- entity identity inside arbitrary sentences;
- temporal qualifiers;
- negation scope.

Pretending otherwise would create false semantic certainty.

Instead, Step 206 introduces a validated semantic contract and explicitly marks
today's claims as not semantically structured.

## Canonical ClaimSemanticStructure

Step 206 adds:

`backend/app/reality/claim_semantic_structure.py`

It defines two states.

### Structured

```json
{
  "status": "structured",
  "subject": "Company X",
  "predicate": "launched",
  "object": "Feature A",
  "structuring_method": "some_semantic_structurer",
  "reason": null
}
```

A structured claim requires:

- non-empty subject;
- non-empty predicate;
- non-empty object;
- non-empty structuring method other than `not_attempted`;
- no reason.

Semantic fields are normalized and bounded.

### Unstructured

```json
{
  "status": "unstructured",
  "subject": null,
  "predicate": null,
  "object": null,
  "structuring_method": "not_attempted",
  "reason": "semantic_structuring_not_attempted"
}
```

An unstructured claim:

- cannot contain subject/predicate/object;
- must use `not_attempted`;
- must carry a non-empty reason.

This makes absence of semantic parsing machine-readable instead of ambiguous.

## EvidenceClaim integration

Every `EvidenceClaim` now has:

`semantic_structure`

The new field is appended after the historical claim fields so existing
positional construction remains compatible.

Legacy code such as:

```python
EvidenceClaim(
    "Company X launched Feature A.",
    ("https://example.test/source",),
)
```

remains valid and automatically receives the canonical unstructured state.

Serialized claims now include the nested semantic-structure object.

## Mapping compatibility

Historical claim-extraction mappings that do not contain
`semantic_structure` remain accepted.

They normalize to:

```text
semantic_structure.status = unstructured
reason = semantic_structuring_not_attempted
```

Mapping-shaped claims that do include semantic structure are validated through
the canonical contract.

Malformed or internally contradictory semantic structures fail closed.

## Current extractor behavior

`EvidenceClaimExtractor` remains a deterministic sentence splitter.

It does not attempt semantic structuring.

Every claim it currently emits therefore has:

```text
status = unstructured
structuring_method = not_attempted
reason = semantic_structuring_not_attempted
```

Deduplication across source-scoped documents preserves the semantic-structure
object together with text, source lineage, and extraction method.

## Entity boundary

Step 204 introduced explicit Reality Entity identity.

Step 206 deliberately does **not** infer:

```text
Reality State entity
→ every extracted claim subject
```

An explicit request entity describes the Reality State investigation scope. It
does not prove that every sentence in every retrieved source has that entity as
its semantic subject.

For example, evidence may discuss:

- competitors;
- regulators;
- partners;
- products;
- historical actors;
- quoted third parties.

Therefore even with:

```json
"entity": "Company X"
```

a current deterministic claim remains unstructured until a semantic structurer
actually establishes its parts.

## Downstream compatibility

The existing linker and conflict detector still operate on claim text and
source references.

Step 206 preserves semantic metadata when mapping-shaped claim results are
reconstructed by those components.

It does **not** change:

- claim/evidence linking logic;
- conflict detection policy;
- source lineage;
- confidence;
- freshness;
- Reality State status.

A future semantic conflict detector may use structured claims, but today's
detector still recognizes only its established explicit-negation pattern.

## Reality State output

Claims in Reality State output now look conceptually like:

```json
{
  "text": "Company X launched Feature A.",
  "source_refs": ["https://example.test/source"],
  "extraction_method": "deterministic_sentence_split",
  "semantic_structure": {
    "status": "unstructured",
    "subject": null,
    "predicate": null,
    "object": null,
    "structuring_method": "not_attempted",
    "reason": "semantic_structuring_not_attempted"
  }
}
```

This is more honest than presenting sentence text as if it were already a
structured semantic fact.

## Future model integration

The `structured` form is intentionally provider-neutral.

A later semantic component may be implemented using:

- Hugging Face transformer models;
- NER/relation extraction pipelines;
- local models;
- external LLM providers;
- fine-tuned models;
- hybrid deterministic/model approaches.

Whatever technology is selected later must produce this canonical contract
rather than leaking provider-specific output into the Reality Layer.

The architecture principle remains:

> Models propose; deterministic contracts constrain and preserve evidence.

## Regression coverage

`backend/tests/test_step206.py` covers:

- canonical unstructured state;
- canonical structured state;
- semantic field normalization and bounds;
- missing/invalid semantic parts;
- invalid structuring method;
- structured/reason contradiction;
- unstructured/semantic-parts contradiction;
- required unstructured reason;
- legacy EvidenceClaim construction;
- structured EvidenceClaim preservation;
- legacy mapping normalization;
- structured mapping round-trip;
- malformed nested semantic structure rejection;
- current extractor's explicit unstructured output;
- deduplication semantic preservation;
- linker mapping reconstruction;
- conflict-detector mapping reconstruction;
- structured-claim compatibility with linking;
- preservation of existing deterministic conflict behavior;
- end-to-end Reality State semantic output;
- proof that explicit entity identity does not auto-fill claim subject;
- preservation of claim text and exact source lineage.

## MVP significance

Step 206 does not yet solve semantic claim extraction.

It creates the stable, validated representation required to solve it properly
in a later step.

The progression is now:

```text
sentence claim
→ explicit semantic-structure state
→ future semantic structurer
→ validated subject/predicate/object
→ stronger semantic linking/conflict/temporal reasoning
```

This is the correct point to introduce advanced semantic technology later,
because the model will have a clear contract to target.

## Deliberate non-goals

Step 206 does not add:

- heuristic subject/predicate/object extraction;
- entity resolution;
- entity-to-claim automatic binding;
- NER;
- relation extraction models;
- embeddings;
- vector search;
- LLM semantic parsing;
- ML/DL inference;
- temporal claim qualifiers;
- semantic conflict judging;
- persistence;
- knowledge graphs;
- factual-truth certification.

Those require separate design and validation.
