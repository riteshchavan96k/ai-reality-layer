# Step 239 — External human-annotated semantic NLI quality benchmark with explicit false-support measurement

## Verified predecessor / why this is correct next work

At branch creation, exact `main` was `6823b3fa0a9b8a9a8dea1d95c885ef30a4050d80`. Step238 was the latest completed scoped engineering milestone: **2,652 backend tests** and **12/12 exact-main push workflows green**, including real original Python.org source capture into genuine pinned quantized ONNX neural NLI shadow inference. Step238 established **actual source-to-model wiring** on three developer-selected claims; it measured **no independently sourced semantic label quality**. No historical Step239 specification existed. Real semantic errors, especially *model entailment on non-entailment evidence*, remain unmeasured. External deployment Step234 is deferred by the user and gate #242 remains OPEN.

## Deliverable

Build a reproducible, **real pretrained ONNX NLI benchmark** against existing human-annotated **Stanford Natural Language Inference (SNLI)** validation examples from Stanford NLP, **not model-fabricated gold labels**. The public corpus is [Stanford NLP SNLI](https://huggingface.co/datasets/stanfordnlp/snli), license CC BY-SA 4.0, citation Bowman et al. 2015 (ACL). The public labels are external crowd annotations and are not independently reaudited by us. The model's training includes SNLI-family data: this **does NOT** establish out-of-distribution performance, dataset independence from model selection, robustness in real sources, or factual truth about the world.

1. **Opt-in-only read** of one *immutable commit-pinned* small public Hugging Face SNLI `plain_text/validation-00000-of-00001.parquet` artifact with verified SHA-256 **`00f5ed8deaed007fef3022f0215b287efbab815b1bb31ac3f3ff4f4129d41ffe`**, no arbitrary dataset URLs or pickle models. Explicit `--live` required before download. Optional `pyarrow` is installed only in a dedicated ML evaluation workflow, not production Docker or default Python backend.
2. Validate the file/dataset schema `premise`, `hypothesis`, `label`; expected 10,000 validation rows and label map **0=entailment, 1=neutral, 2=contradiction**, refusing invalid/unlabeled/nonfinite/oversized and mutated data. Use deterministic fixed sampling of 40 first eligible rows *per class* in original dataset row order (120 total). The subset is **not random or representative**; clearly disclose sampling bias. No developer-generated "gold" labels and no test-claim paraphrase promotion.
3. Execute the **real pinned Step237 model** (revision `b95119c`, reviewed ONNX quantized SHA `44391a5241a62e0083c1a8899a71e69a092b95aea5ba89e14062925468eceac7`) on source premise and claim hypothesis in original order. Output only class-count confusion matrix, exact integer denominators, per-class precision/recall, conditional overall 120-case accuracy, and **false-entailment on human-labeled neutral/contradiction cases**. Scores are measured on a *known public evaluation subset*, not population/world factual accuracy. Never print raw dataset sentences, reviewer identity, credentials or untrusted model errors.
4. Programmatic error-rate gating: malformed predictions, incomplete/failure rows, illegal label mappings, wrong digest/revision, unknown model decisions, duplicate pair IDs or label leak must fail the benchmark, **not silently decrease denominators**. The model accuracy itself is **observational**, without inventing a target/declaring "production ready." A significant false-entailment count must be preserved and reported.
5. Add adversarial unit tests without optional model dependencies; one new independent **13th GitHub workflow** installing optional evaluation dependencies and running **genuine human-annotated dataset + real pretrained model**. Require exact final main SHA **13/13 success** and a logged human-labeled externally-sourced evaluation scorecard.
6. No production API or model-router changes. All model-driven claim support promotion remains explicitly disallowed, source assurance and AI-claim consumer remain unchanged, and Step234 externally hosted release gate #242 remains open.

## Limitations

- SNLI is largely caption / ordinary sentence-pair semantics. A human-labeled premise--hypothesis entailment judgement is not real-world factual truth.
- SNLI crowd labels are externally authored; we did **not** personally recruit/verify independent annotators. The selected model is trained on SNLI-family data, so this cannot be called a *model-family-independent* held-out generalization study.
- A fixed 40-per-class first-eligible slice is balanced but convenience-selected. Do not claim its scores are representative of the 10,000-row dataset, production inputs, or all language.
- This benchmark evaluates **language entailment** only; it does not validate source authorship, temporal state, evidence independence, broad publisher applicability, or end-user safety.
- Real human-authored *domain-specific* source evidence labels remain future work.

## Status

**In progress** until the actual real model runs against the checked external dataset and all **13 final-main `push` workflows** pass on the same exact final SHA. Scoped milestone success is **measured and honestly reported external NLI evaluation only**, not verified real-world factual accuracy, source reliability or neural production authority.
