# Step 237 — Real neural NLI shadow inference, zero authority promotion

## Verified predecessor and scope selection

The verified last completed milestone is Step 236: exact final-main commit `499c6a9ed26b23242ae5a39b513fb58028b270aa` passed 2,585 backend tests and ten independent GitHub Actions push workflows. Step 236 defined a frozen 20-case developer-authored *semantic candidate* benchmark, with exactly 3 deterministic text-only alignments, 3 contradictions and 14 abstentions; no independent human-reviewed labels were supplied. There was no preexisting Step 237 spec. Step 234 external hosting remains deferred by the project owner, [release gate #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242) stays OPEN.

## Actual product gap

Our semantic verification system has a rigorous deterministic/observed-source baseline but **no genuine neural semantic inference**. Develop the first replaceable pretrained NLI model experiment in strict **shadow mode**. Run a real model on the exact frozen claim–evidence pairs using evidence as **premise**, claim as **hypothesis**, recording entailment/contradiction/neutral model predictions alongside the real deterministic baseline. This improves our ability to *measure* model capabilities before authorizing any model-driven product decisions.

## Intended implementation / acceptance

1. Isolated optional Python/ONNX CPU adapter using actual reviewed [cross-encoder/nli-MiniLM2-L6-H768](https://huggingface.co/cross-encoder/nli-MiniLM2-L6-H768), an Apache-2.0 neural Transformer trained on SNLI/MultiNLI. Download only specifically allowlisted model assets when `--live` is requested; no model network activity on module import or ordinary API execution. Pin immutable model revision and SHA-256 of the quantized ONNX weights, reject mismatches and incorrect label mapping.
2. Use an actual Hugging Face tokenizer and onnxruntime CPU weights, validate bounded text, model input schema and finite 3-class logits, map exact published `contradiction/entailment/neutral` output labels, and return model scores explicitly labeled uncalibrated. No model prompt execution, arbitrary repo IDs, Python pickle weights, GPU allocation, arbitrary URLs or production host change.
3. Independently test adapter validation, model-output tampering, label ordering and shape mismatch, budget handling, unavailable dependencies, model download opt-in, malformed paths, and absence of production API authority. Preserve 2,585 previous backend tests and ten workflows.
4. An independent 11th GitHub-hosted workflow installs optional dependencies, retrieves the pinned **real** model, validates the actual SHA-256 and runs **all 20** frozen cases with actual ONNX inference. CI must show real model and scorecard with no fabricated independent human gold or held-out general factual accuracy.
5. Produce a digest-bound no-truth-claims shadow comparison containing only case IDs, model vs deterministic predictions and fixed model metadata (no arbitrary source excerpts or secrets). Model disagreement is informative, not proof of error. **No model output can change `POST /api/v1/reality-state/claim`, `AIClaimGateDecision`, original-source allowlist/assurance, action permissions or the root model registry.**
6. Finalize only if all eleven workflows on exact final merged-main SHA are green, with inspected logs showing real ONNX execution. Record any inaccurate model outputs explicitly; do not relabel benchmarks for flattering results.

## Truth and deployment boundaries

- 20 pairs remain developer-authored and do NOT include independent human semantic or factual labels, representative sampling, or captured original publisher bytes. The model **cannot authenticate source authorship** or claim truth from this dataset.
- Neural softmax scores are *not statistically calibrated probability of factual truth*. An entailment model prediction is **not** a permissible Reality State support elevation.
- Independent human review, external live-world semantic accuracy, broader publisher coverage, and eventual carefully gated integration remain future milestones.
- No public deployment is requested or performed. Step 234 gate #242 remains open.

## State

## Verified Step 237 implementation acceptance (2026-10-13)

The new [Step237 real neural NLI implementation PR #256](https://github.com/riteshchavan96k/ai-reality-layer/pull/256) merged to exact `main` SHA **`d48b7945a78ed4c7b7aef52f1b7617a5fc5164d0`**. All **eleven** independent GitHub-hosted `push` workflows completed successfully, checked against the same exact main commit:

- [Backend 38416933299](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38416933299): actual CI logs **2,619 tests passed in 8.26s**.
- [Step237 genuine neural inference 38416933361](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38416933361): actual CI logs **69 Step236+237 tests passed**, pinned Hugging Face model successfully acquired and SHA-256 checked, ONNX CPU neural inference actually executed for **20/20** frozen Step236 pairs. Neural model classifications: **11 entailment, 5 contradiction, 4 neutral**; existing deterministic baseline on same cases: **3 bounded textual alignments, 3 bounded textual contradictions, 14 abstentions**. The ONNX quantized weights SHA-256 was **`44391a5241a62e0083c1a8899a71e69a092b95aea5ba89e14062925468eceac7`**, revision `b95119c`.
- Preserved independently green historical push workflows: [Step231 authenticated Docker 38416933463](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38416933463), [original claim 38416933309](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38416933309), [Step222 38416933364](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38416933364), [Step226 38416933246](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38416933246), [Step227 38416933336](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38416933336), [Step232 38416933396](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38416933396), [Step233 38416933318](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38416933318), [Step235 38416933623](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38416933623), [Step236 38416933258](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38416933258).

**This establishes genuine model execution and safely isolated shadow comparison, NOT independently measured accuracy**. None of the developer-authored 20 paired excerpts carries authenticated original-source truth; no real human-reviewed semantic gold is present. A greater number of model entailments is not a model quality victory. Production strict source decisions, claim API, and downstream AI-client authorization are unchanged. This engineering milestone is complete within scope, while the next scientific validation (real independent labels, diverse original-source captures and holdout evaluation) remains pending. External deployment gate #242 stays open.

## Final acceptance

**✅ Step 237 scoped neural NLI shadow engineering complete** based on independently checked exact-main implementation evidence, with documentation-only follow-up requiring its own GitHub CI recheck.


