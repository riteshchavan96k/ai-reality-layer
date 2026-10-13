# Step 236 — Blind semantic annotation protocol and strict limits

## What you are reviewing

Twenty short **candidate** claim/source-text pairs, NOT a sampled accuracy benchmark. Twelve are **developer-created** reuses of the Step 232 controlled source-identity challenge and contain genuine publisher **URL strings** but **not independently authenticated original publisher text**. Some candidate passages are deliberately *forgeries* for negative testing. Eight additional pairs are explicitly **fictional exercises**. Do **not** assume a source URL certifies the excerpt, and do not interpret a reviewer's entailment judgment as a fact about the world.

This review answers only: *Given the displayed candidate evidence sentence, is the displayed claim semantically entailed, contradicted, neutral, or too uncertain to label?* Assess temporal scope, negation, entity identity and modality; do not consult model outputs or a prior developer answer key.

## Generate a blind packet locally (zero source network requests)

```bash
python -m backend.app.evaluation.step236_semantic_baseline --summary-only
python -m backend.app.evaluation.step236_semantic_baseline --summary-only --blind-packet /tmp/arl-step236-review-packet.json
```

The exported packet includes the frozen dataset SHA-256 and each short pair; **no semantic gold labels or parser decisions**. Never put reviewer names, contact information, unpublished company details or model credentials inside the project or GitHub.

## Independent review procedure (outside this code; NOT YET PERFORMED)

1. Have two humans **not involved in constructing the candidate corpus, selecting thresholds, or viewing the benchmark predictions** review the same frozen cases separately. Record consent and the review protocol privately. A GitHub commit, chatbot, or self-declared reviewer ID does not authenticate a human or their independence.
2. Each independent reviewer assigns one of `entails`, `contradicts`, `neutral`, `uncertain`. They judge the supplied text only, not publisher truth. They should not see the other's responses before submitting.
3. Maintain an external review-audit record (not in the public repository) for reviewer identity checks, review dates, independence from dataset/model authorship, dataset SHA and permitted content usage. This must be genuinely collected; do not fill placeholders and claim they are verified.
4. Resolve any reviewer disagreements in a separate adjudication record, without changing the frozen input or quietly rewriting an existing answer; introduce a new dataset/version if needed. The current runner **refuses** to emit conditional scores for incomplete or disputed pairs.
5. Collect much broader **authorized, independently captured** real-source claims and holdout labels before training, deploying, or making field-accuracy assertions. This 20-case set is just a reproducible foundation, NOT representative.
6. Compare deterministic and neural NLI predictions on a separate held-out dataset. Count false support, contradiction precision and recall, abstentions and per-slice performance. Benchmark neural models in shadow mode until permitted to influence production decisions.

## Offline submission format for *conditional* reviewer consensus only

The schema is a JSON object with `schema_version="1.0"`, `dataset_sha256` equal to the blind-packet digest, `review_identity_audit_status="not_independently_verified"`, and an `annotations` list. Each list entry has exactly `case_id`, `reviewer_id` (pseudonymous, three–64 ASCII alphanumeric/underscore/hyphen characters), and `label` in the enum above.

For a fully supplied input there must be exactly two distinct reviewer IDs **for every case** with agreeing labels. Any missing or disputed cases produces an incomplete/disputed response without conditional metrics. Duplicate, unknown, malformed or drifted dataset inputs fail closed.

```bash
python -m backend.app.evaluation.step236_semantic_baseline \
  --summary-only --review-file /path/to/privately-collected-two-reviewer-labels.json
```

**The program cannot authenticate human reviewers.** Even with complete consistent self-declared labels, its status is always `conditional_consensus_unverified_reviewer_identities`, and `independent_human_labels_verified=false` and `population_accuracy_established=false`. Any real independently reviewed label release must be verified and audited outside this module; the CLI will not fabricate an attestation.

## Measured engineering-only scorecard

GitHub-hosted Step236 PR CI reproduced 20 text pairs: **3 bounded textual alignments, 3 bounded textual contradictions, 14 abstentions**, with exact corpus hash `5987acb4fb6d33b98c079c545370d9f3dfd195bcefd7da3179f0c8b184e132fa`. At least **two of the three textual alignments** correspond to deliberately forged or source-misattributed candidate excerpts. This is an intentional demonstration of text-only model limitations, **not actual strict HTTPS product false support**: the production source reader would still need to independently match original source bytes and pass its own strict controls.

Machine-readable scorecard: [STEP_236_BASELINE.json](STEP_236_BASELINE.json). Changes to any challenge text under the same corpus version are rejected by a pinned SHA-256; a new version must be explicitly reviewed.

Step 234 external HTTPS hosting release issue #242 stays open and deferred until core development is ready. No Hugging Face, LLM, neural inference or deployment is added here.
