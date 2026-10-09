# Step 219 — Conservative Explicit-Entity Evidence Relevance Gate

## Verified motivation

Step 218 created a 48-case offline publisher-anchored adversarial benchmark.
Before this milestone, **8/8 wrong-topic official-source cases** received
`supported` even though the supplied document described a different
software release than the explicit target entity. The previous
`RealityConfidenceSignalAggregator` only checked coverage of supplied
source references, reported observation age and explicit negation conflict
count; it did not check target-entity alignment of the claims being supported.

A URL's validity does NOT prove that its content belongs to the task or that
the supplied text truly came from that URL. This milestone addresses one
**narrow measured gap** — textual entity alignment — without pretending to
solve the still-measured URL-content forgery or semantic entailment gaps.

## Implementation

Production logic is limited to:

- `backend/app/reality/entity_relevance.py`: a small deterministic
  `explicit_entity_link_alignment(entity, linking)` helper that
  validates the canonical explicit entity identity, requires usable
  nonempty linked-claim references, and checks **every** linked
  `claim_text` for an entire textual match to the explicit entity.
- `backend/app/reality/confidence_signal_aggregator.py`: an optional,
  keyword-only `entity` argument; when the entity is explicitly specified,
  a failed entity alignment forces `uncertain` without modifying original
  source-link coverage, freshness count, candidate conflict count, or reason.
- `backend/app/orchestrator/orchestrator.py`: the submitted-evidence
  Reality State path forwards explicit `entity` to the aggregator.
- `backend/app/orchestrator/pipeline.py`: the retrieval-backed Reality
  State path forwards explicit `entity` to the same aggregator.

Both paths use the **same relevance check**. Legacy calls lacking
an explicit entity preserve the original confidence behavior and the
public API request/response shape is unchanged.

### Matching policy — safety details

Full explicit entity identity is matched within each linked claim after
Unicode-aware case folding and whitespace normalization. Word, period and
hyphen boundaries prevent substring mistakes:

- `Python 3.13.0` matches `Python 3.13.0 was released.`.
- `Python 3.13` **does not** match `Python 3.13.0`.
- `Go 1.24` **does not** match `Go 1.24.0`.
- `Company X` **does not** match `Company XYZ`.

A single matching claim cannot paper over other unrelated linked
claims: every linked claim must match to allow a `supported` result.
This is intentionally conservative and can create false abstentions for
pronouns, abbreviated entities, mixed-context documents or different
names for the same entity. Such misses require better future evaluation
rather than loosening the matcher without evidence.

When the caller supplies an entity, signals record either
`explicit_entity_not_aligned_with_all_linked_claims` or
`explicit_entity_text_alignment_only`. The second signal **does not
claim factual verification**; it means only the literal condition passed.

The gate never fetches a publisher URL, checks original document
content, cryptographically authenticates the publisher, or evaluates
semantic entailment. A **forged statement that includes the exact
requested entity** may still be classified as structurally
`supported`. This is explicitly tested.

## Evaluation discipline

- **Do not rewrite the recorded historical Step 218 baseline.**
  `docs/STEP_218_BASELINE.json` remains a snapshot of the pre-gate
  implementation with 16/40 false supports and 8/8 wrong-topic supports.
  Its regression test now asserts the original historical values
  rather than incorrectly expecting them to match improved code.
- Preserve the Step 217 independently labeled fictional baseline
  unchanged. The full CI must continue to replay it.
- Add a new `docs/STEP_219_SCORECARD.json` and
  `docs/STEP_219_SCORECARD.md` based on the **actual GitHub-hosted**
  Step 218 benchmark run after the relevance gate, not guessed numbers.
  Record both improved and unchanged failure classes.
- Add a Step 219 scorecard parity regression ensuring the current product
  produces exactly the committed values on the fixed official-source
  dataset, while Step 218 remains historical.

### Acceptance criteria

1. In Step 218's eight wrong-topic cases, no case should receive
   `supported` when the linked text lacks the exact explicit entity.
2. The eight relevant publisher-date cases should still return
   structurally `supported` on the narrow offline set.
3. The eight forged same-URL cases remain visibly unsafe rather than
   falsely claiming the matcher verifies authenticity.
4. Existing conflict, freshness and no-explicit-entity behavior must
   stay compatible. Retrieving and submitted-evidence paths must agree.
5. Fully preserve historical Step 217 and 218 baseline numbers, and
   publish a new post-gate scorecard with real replay observations.
6. Host Python 3.13 backend compile, full pytest, and both benchmark
   summaries must pass on the feature head, merged main, and final
   status-sync SHA before completion is claimed.

**Important:** The success criterion is correct improvement on the
explicit-entity text-alignment failure, NOT verified publisher-source
authenticity or full semantic query relevance.

## Product direction after Step 219

A future separately identified work item must address actual
source-content verification and *relevance beyond literal mentions*,
preferably with immutable official-source captures and blinded,
independently reviewed examples. An attacker can prepend the correct
entity string to misleading evidence. We must not infer verified truth
from a matching identifier.

No LLM, Hugging Face model, knowledge graph, network provider,
database, or public API schema change was added here. The decision
to use such technologies will depend on measured improvements on
separate evaluation data.

## Replay

From the repository root:

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
```

Detailed benchmark scenarios can be saved with
`python -m backend.app.evaluation.official_source_quality_benchmark --output /tmp/step219-details.json`.
