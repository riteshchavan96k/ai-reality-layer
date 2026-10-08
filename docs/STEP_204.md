# Step 204 — First-Class Reality Entity Foundation

## Objective

Move AI Reality Layer beyond task-only snapshots by introducing the first
canonical representation of the real-world entity being investigated.

The MVP specification has always defined `Entity` as a core object and lists
`entity` in the expected structured output. Through Step 203, the live
repository had no entity implementation at all.

Step 204 establishes that missing foundation without pretending that semantic
entity extraction or entity resolution already exists.

## Product gap

Before Step 204, a Reality State contained:

- task;
- evidence;
- claims;
- claim/evidence links;
- provenance;
- source observation;
- freshness;
- conflicts;
- confidence.

But it did not contain a first-class entity.

For a request such as:

```text
What is the current status of Company X?
```

the string `Company X` existed only inside free-form task/claim text.

That prevents the system from safely evolving toward:

- entity-scoped Reality States;
- entity resolution;
- claim subject identity;
- Reality State versioning per entity;
- temporal histories;
- Reality Graph relationships.

## Design principle: explicit before inferred

Step 204 does **not** infer an entity from arbitrary task text.

No regex, heuristic, LLM, embedding model, NER model, or external entity
resolver is introduced.

Instead, callers may provide an optional explicit entity name.

When provided:

```json
{
  "status": "specified",
  "name": "Company X",
  "identification_method": "explicit_input"
}
```

When omitted:

```json
{
  "status": "unspecified",
  "name": null,
  "identification_method": "not_provided"
}
```

This prevents the deterministic MVP from fabricating entity identity.

## Canonical RealityEntity

Step 204 adds `backend/app/reality/reality_entity.py`.

The canonical immutable entity contract contains:

- `status`: `specified` or `unspecified`;
- `name`: explicit normalized name or `None`;
- `identification_method`: `explicit_input` or `not_provided`.

A specified entity requires:

```text
non-empty normalized name
identification_method == "explicit_input"
```

An unspecified entity requires:

```text
name is None
identification_method == "not_provided"
```

Explicit names are bounded to 500 characters and surrounding whitespace is
removed.

## Reality State integration

`RealityState` now contains a typed `RealityEntity` and serializes it as the
top-level `entity` field.

The serialized shape is now conceptually:

```text
Reality State
├── status
├── task
├── entity
├── evidence
├── claims
├── claim_evidence_linking
├── source_provenance
├── source_observation
├── freshness
├── conflicts
└── confidence_signals
```

The entity does not alter confidence, evidence quality, retrieval, or claim
semantics in this step.

## Backward compatibility

Older Python callers that do not supply an entity remain valid.

Older mapping-shaped Reality States that predate Step 204 and have no
`entity` field normalize to:

```text
status = unspecified
name = None
identification_method = not_provided
```

The `RealityState` dataclass places the new defaulted entity field after the
existing defaulted constructor fields so historical positional constructor
arguments retain their original meaning.

## API integration

Both Reality State API request types now accept:

```json
"entity": "Company X"
```

as an optional field:

- `POST /api/v1/reality-state`;
- `POST /api/v1/reality-state/evidence`.

The entity name is normalized at the request boundary.

The canonical response model now exposes a typed `RealityEntityResponse`.

Requests that omit entity remain valid and receive an explicit
`unspecified` entity in the resulting Reality State.

## Retrieval-backed path

The retrieval-backed Reality State builder stores the canonical entity in the
orchestration analysis state and passes it into final Reality State assembly.

The explicit entity is metadata for the Reality State in Step 204. It does not
yet rewrite or augment the retrieval query.

That query-planning behavior should only be added when the product semantics
for entity-scoped retrieval are explicitly designed.

## Submitted-evidence path

`build_reality_state_from_evidence()` also accepts the optional explicit
entity and preserves it in the same canonical output.

No source, claim, or provenance data is rewritten based on the supplied entity.

## Regression coverage

`backend/tests/test_step204.py` covers:

- explicit entity normalization;
- explicit unspecified representation;
- typed/string/mapping normalization;
- blank and oversized entity rejection;
- inconsistent entity-state rejection;
- legacy Reality State mapping compatibility;
- explicit entity preservation in Reality State validation;
- retrieval-backed entity propagation;
- no heuristic entity inference from task text;
- submitted-evidence entity propagation;
- unspecified behavior when omitted;
- request-boundary normalization;
- API rejection of invalid entity input;
- both HTTP handler paths;
- typed response-schema exposure;
- OpenAPI entity documentation;
- legacy Python builder calls without entity.

The Step-180 request-shape regression is updated intentionally because entity
is now an optional retrieval-endpoint field while submitted evidence documents
remain forbidden on that endpoint.

## Architectural significance

Step 204 is the first move from the long contract-hardening sequence back into
substantive product capability.

It establishes the stable identity slot needed before later work on:

- entity type;
- aliases;
- canonical entity identifiers;
- entity extraction;
- entity resolution;
- claim subjects;
- persistent entity histories;
- temporal Reality States;
- Reality Graph relationships.

Those capabilities are intentionally not bundled into this step.

## Deliberate non-goals

Step 204 does not add:

- heuristic entity parsing;
- NER;
- embeddings;
- LLM entity extraction;
- entity resolution;
- canonical external identifiers;
- aliases;
- entity type inference;
- database persistence;
- knowledge graphs;
- entity-aware retrieval-query rewriting;
- semantic claim extraction;
- ML/DL;
- new external providers.

Those require separate design and validation steps.
