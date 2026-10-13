"""Step 237: optional real neural entailment/contradiction/neutral shadow inference.

This code is NEVER invoked by production API or model routing. Explicit
--live is required for Hugging Face downloads. Candidate input is not proof
of original-source bytes. NLI probabilities are uncalibrated, not factual truth.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

from backend.app.evaluation.step236_semantic_baseline import (
    baseline_report, load_candidates,
)

MODEL_REPO = "cross-encoder/nli-MiniLM2-L6-H768"
# Repository history documents this immutable commit prefix (2025-04-15).
MODEL_REVISION = "b95119c"
ONNX_FILE = "onnx/model_quint8_avx2.onnx"
ONNX_SHA256 = "44391a5241a62e0083c1a8899a71e69a092b95aea5ba89e14062925468eceac7"
ALLOWED_ASSETS = (ONNX_FILE, "tokenizer.json", "config.json")
EXPECTED_LABELS = ("contradiction", "entailment", "neutral")
MODEL_PREDICTIONS = frozenset(EXPECTED_LABELS)
MAX_TEXT_CHARS = 500
MAX_PAIR_TOKENS = 256
MODEL_FILE_MAX_BYTES = 90_000_000
HEX_SHA = re.compile(r"[a-f0-9]{64}")


class ShadowNLIError(ValueError):
    """Safe, fixed failure without remote data or local private paths."""


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ShadowNLIError(message)


def _hash_verified_weights(file_path: Path) -> str:
    _require(file_path.is_file(), "missing_model_asset")
    _require(file_path.stat().st_size <= MODEL_FILE_MAX_BYTES, "model_asset_oversized")
    digest = sha256()
    with file_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    h = digest.hexdigest()
    _require(h == ONNX_SHA256, "model_weights_digest_mismatch")
    return h


def _validate_label_config(configuration: dict) -> None:
    _require(type(configuration) is dict, "model_config_invalid")
    raw = configuration.get("id2label")
    _require(type(raw) is dict and len(raw) == 3, "model_labels_missing")
    _require(tuple(raw.get(str(i)) for i in range(3)) == EXPECTED_LABELS,
             "model_label_map_mismatch")
    _require(configuration.get("model_type") == "roberta", "model_type_unexpected")


def _validated_pair(premise: str, hypothesis: str) -> None:
    for text in (premise, hypothesis):
        _require(type(text) is str and 0 < len(text) <= MAX_TEXT_CHARS
                 and text.strip() == text and "\x00" not in text
                 and "\r" not in text, "invalid_model_input")


def _normalized_logits(logits: Any) -> tuple[str, dict[str, float]]:
    """Validate real scores rather than claiming uncalibrated logits are truth."""
    try:
        # Numpy ONNX arrays and plain Python matrices share this interface;
        # unit tests deliberately do not install optional heavy ML packages.
        rows = list(logits)
        _require(len(rows) == 1, "invalid_model_output_shape")
        values = list(rows[0])
        _require(len(values) == 3 and all(
            type(x) in (int, float) or hasattr(x, "item") for x in values
        ), "invalid_model_output_shape")
        scores = [float(x) for x in values]
        _require(all(math.isfinite(x) for x in scores), "non_finite_model_scores")
        max_value = max(scores)
        exp = [math.exp(x - max_value) for x in scores]
        total = sum(exp)
        _require(math.isfinite(total) and total > 0, "invalid_normalization")
        probs = [x / total for x in exp]
        _require(all(0.0 <= x <= 1.0 and math.isfinite(x) for x in probs),
                 "invalid_probability")
        idx = max(range(3), key=lambda x: probs[x])
        return EXPECTED_LABELS[idx], {
            label: round(probs[i], 6)
            for i, label in enumerate(EXPECTED_LABELS)
        }
    except (OverflowError, ValueError, TypeError) as error:
        if isinstance(error, ShadowNLIError):
            raise
        raise ShadowNLIError("invalid_model_scores") from None


class ONNXNLIShadow:
    """Real ONNX CPU inference, explicitly constructed and never authoritative."""

    def __init__(self, model_path: Path, tokenizer_path: Path, config_path: Path):
        _hash_verified_weights(model_path)
        _require(tokenizer_path.is_file() and config_path.is_file(), "missing_model_asset")
        _require(tokenizer_path.stat().st_size <= 3_000_000
                 and config_path.stat().st_size <= 10_000, "asset_too_large")
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ShadowNLIError("invalid_model_config") from None
        _validate_label_config(config)

        try:
            from tokenizers import Tokenizer
            import onnxruntime as ort
            self._tokenizer = Tokenizer.from_file(str(tokenizer_path))
            self._tokenizer.enable_truncation(max_length=MAX_PAIR_TOKENS)
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 2
            opts.inter_op_num_threads = 1
            self._session = ort.InferenceSession(
                str(model_path), sess_options=opts, providers=["CPUExecutionProvider"]
            )
            self._inputs = tuple(x.name for x in self._session.get_inputs())
        except (ImportError, OSError, ValueError, RuntimeError):
            raise ShadowNLIError("model_runtime_unavailable_or_invalid") from None

        _require(
            set(self._inputs) in (
                {"input_ids", "attention_mask"},
                {"input_ids", "attention_mask", "token_type_ids"},
            ), "unsupported_onnx_input_schema",
        )

    def predict(self, premise: str, hypothesis: str) -> dict[str, Any]:
        """Evidence is premise and claim is hypothesis, never reversed."""
        _validated_pair(premise, hypothesis)
        try:
            import numpy as np
            tokens = self._tokenizer.encode(premise, hypothesis)
            _require(1 <= len(tokens.ids) <= MAX_PAIR_TOKENS, "token_budget_exceeded")
            arrays = {
                "input_ids": np.asarray([tokens.ids], dtype=np.int64),
                "attention_mask": np.asarray([tokens.attention_mask], dtype=np.int64),
                "token_type_ids": np.asarray([tokens.type_ids], dtype=np.int64),
            }
            result = self._session.run(None, {
                name: arrays[name] for name in self._inputs
            })
            _require(type(result) is list and len(result) == 1,
                     "invalid_onnx_output_count")
            label, scores = _normalized_logits(result[0])
        except (OSError, RuntimeError, KeyError, TypeError):
            raise ShadowNLIError("model_inference_failed") from None
        return {
            "predicted_relation": label,
            "uncalibrated_model_scores": scores,
            "not_a_truth_probability": True,
            "not_authorized_to_support_claim": True,
        }


def load_reviewed_model(*, cache_dir: Path, live: bool) -> ONNXNLIShadow:
    """Explicit model acquisition with pinned revision + exact ONNX SHA-256."""
    _require(live is True, "live_model_acquisition_not_authorized")
    _require(isinstance(cache_dir, Path), "invalid_model_cache")
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        raise ShadowNLIError("optional_model_dependencies_unavailable") from None
    files = {}
    try:
        for filename in ALLOWED_ASSETS:
            files[filename] = Path(hf_hub_download(
                repo_id=MODEL_REPO, filename=filename, revision=MODEL_REVISION,
                cache_dir=str(cache_dir),
            ))
    except Exception:
        raise ShadowNLIError("reviewed_model_download_unavailable") from None
    return ONNXNLIShadow(
        files[ONNX_FILE], files["tokenizer.json"], files["config.json"]
    )


def evaluate_shadow(model: Any, manifest: dict) -> dict[str, Any]:
    baseline = baseline_report(manifest)
    _require(baseline["candidate_count"] == 20
             and baseline["independent_human_labels_verified"] is False,
             "invalid_shadow_candidate_set")
    old = {x["case_id"]: x["prediction"] for x in baseline["results"]}
    new_results = []
    for case in manifest["cases"]:
        response = model.predict(case["evidence_excerpt"], case["claim"])
        _require(type(response) is dict
                 and response.get("predicted_relation") in MODEL_PREDICTIONS
                 and response.get("not_authorized_to_support_claim") is True
                 and response.get("not_a_truth_probability") is True,
                 "invalid_shadow_prediction")
        new_results.append({
            "case_id": case["id"],
            "deterministic_text_only": old[case["id"]],
            "neural_shadow_prediction": response["predicted_relation"],
            "neural_prediction_authorized": False,
        })
    return {
        "milestone": "step237_real_neural_nli_shadow",
        "candidate_count": len(new_results),
        "candidate_dataset_sha256": baseline["dataset_sha256"],
        "neural_model_executed": True,
        "model_repository": MODEL_REPO,
        "model_revision": MODEL_REVISION,
        "model_format": "quantized_onnx_cpu",
        "model_weights_sha256": ONNX_SHA256,
        "neural_label_counts": dict(sorted(Counter(
            x["neural_shadow_prediction"] for x in new_results
        ).items())),
        "text_baseline_counts": baseline["prediction_counts"],
        "unverified_human_accuracy": None,
        "independent_human_labels_verified": False,
        "original_publisher_bytes_verified_for_this_dataset": False,
        "semantically_entailed_in_production": False,
        "model_predictions_can_authorize_claim_support": False,
        "production_api_changed": False,
        "externally_deployed": False,
        "results": new_results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="Explicitly download and execute one pinned real ONNX NLI model.")
    parser.add_argument("--cache-dir", type=Path, default=Path("/tmp/arl-step237-hf-cache"))
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("no implicit model download/inference; --live required")
    try:
        model = load_reviewed_model(cache_dir=args.cache_dir, live=True)
        result = evaluate_shadow(model, load_candidates())
        if args.summary_only:
            result.pop("results")
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ShadowNLIError, OSError, ValueError, TypeError):
        print("Step 237 shadow-model experiment failed; no factual authority granted")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
