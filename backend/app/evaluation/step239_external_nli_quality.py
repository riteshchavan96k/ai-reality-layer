"""Step239: actual pretrained NLI quality on external crowd-labeled SNLI data.

NO production API/claim decisions. Opt-in download of one SHA256-pinned,
CC-BY-SA-4.0 Stanford SNLI validation Parquet and SHA-verified Step237 neural
weights. Scores refer only to a biased, fixed 120-item external validation
slice, NOT domain factual truth or independently audited user label quality.
Never print sentence texts, annotations, credentials or untrusted errors.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable

from backend.app.evaluation.step237_nli_shadow import (
    EXPECTED_LABELS, MODEL_REPO, MODEL_REVISION, ONNX_SHA256,
    _validated_pair, load_reviewed_model,
)

DATASET_REPO = "stanfordnlp/snli"
DATASET_REVISION = "cdb5c3d"
DATASET_FILE = "plain_text/validation-00000-of-00001.parquet"
DATASET_SHA256 = "00f5ed8deaed007fef3022f0215b287efbab815b1bb31ac3f3ff4f4129d41ffe"
DATASET_LICENSE = "CC-BY-SA-4.0"
LABEL_IDS = {0: "entailment", 1: "neutral", 2: "contradiction"}
LABELS = ("entailment", "neutral", "contradiction")
EXPECTED_DATASET_ROWS = 10_000
PER_CLASS = 40
EXPECTED_EVALUATED = len(LABELS) * PER_CLASS
MAX_DATASET_BYTES = 2_000_000


class ExternalEvaluationError(ValueError):
    """Fixed diagnostic, not raw input/model text."""


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ExternalEvaluationError(code)


def verified_parquet_file(file: Path) -> Path:
    require(isinstance(file, Path) and file.is_file(), "dataset_file_missing")
    require(0 < file.stat().st_size <= MAX_DATASET_BYTES, "dataset_file_bad_size")
    digest = sha256()
    with file.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 256), b""):
            digest.update(chunk)
    require(digest.hexdigest() == DATASET_SHA256, "dataset_sha256_mismatch")
    return file


def load_external_human_labeled_rows(file: Path) -> list[dict[str, Any]]:
    """Read only SHA256-pinned validation split. No executable dataset scripts."""
    verified_parquet_file(file)
    try:
        import pyarrow.parquet as parquet
        table = parquet.read_table(file)
    except (ImportError, OSError, ValueError, RuntimeError):
        raise ExternalEvaluationError("dataset_parquet_invalid_or_unavailable") from None
    require(set(table.column_names) == {"premise", "hypothesis", "label"},
            "dataset_schema_mismatch")
    require(table.num_rows == EXPECTED_DATASET_ROWS, "validation_split_row_count_mismatch")
    rows = table.to_pylist()
    require(len(rows) == EXPECTED_DATASET_ROWS, "dataset_row_count_mismatch")
    return rows


def select_fixed_balanced_subset(
    rows: Iterable[dict[str, Any]], *, per_label: int = PER_CLASS,
) -> list[dict[str, Any]]:
    """First N eligible rows per label, preserving original validation order.

    Not random; this slice can be systematically biased. Reject invalid
    pair content rather than converting altered labels into our gold.
    """
    require(type(per_label) is int and 1 <= per_label <= PER_CLASS, "bad_sample_size")
    selection: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    seen_pairs: set[str] = set()
    for original_index, raw in enumerate(rows):
        require(type(raw) is dict and set(raw) == {"premise", "hypothesis", "label"},
                "external_row_schema_invalid")
        label_code = raw["label"]
        require(type(label_code) is int and label_code in {-1, 0, 1, 2},
                "external_label_code_invalid")
        if label_code == -1:
            continue  # Corpus explicitly defines -1 as no usable consensus.
        label = LABEL_IDS[label_code]
        if counts[label] >= per_label:
            continue
        premise, hypothesis = raw["premise"], raw["hypothesis"]
        # Filter beyond the 500-character bounded neural model contract, but
        # never fabricate a new hypothesis or silently swap pair direction.
        if (
            type(premise) is not str or type(hypothesis) is not str
            or not 0 < len(premise) <= 500
            or not 0 < len(hypothesis) <= 500
            or premise.strip() != premise or hypothesis.strip() != hypothesis
            or "\r" in premise or "\r" in hypothesis
            or "\x00" in premise or "\x00" in hypothesis
        ):
            continue
        key = sha256((premise + "\x00" + hypothesis).encode("utf-8")).hexdigest()
        require(key not in seen_pairs, "duplicate_selected_semantic_pair")
        seen_pairs.add(key)
        selection.append({
            "row_index": original_index, "premise": premise,
            "hypothesis": hypothesis, "human_label": label,
        })
        counts[label] += 1
        if all(counts[code] == per_label for code in LABELS):
            break
    require(len(selection) == per_label * len(LABELS)
            and all(counts[k] == per_label for k in LABELS),
            "insufficient_balanced_labeled_cases")
    return selection


def score_predictions(
    selected: list[dict[str, Any]], predictions: list[str],
) -> dict[str, Any]:
    require(type(selected) is list and type(predictions) is list
            and len(selected) == len(predictions) == EXPECTED_EVALUATED,
            "missing_or_extra_inference_predictions")
    matrix = {gold: {predicted: 0 for predicted in LABELS} for gold in LABELS}
    ids: set[int] = set()
    for item, prediction in zip(selected, predictions):
        require(type(item) is dict and set(item) == {
            "row_index", "premise", "hypothesis", "human_label"
        }, "invalid_reference_case")
        require(type(item["row_index"]) is int and item["row_index"] >= 0
                and item["row_index"] not in ids, "invalid_or_duplicate_row_index")
        ids.add(item["row_index"])
        require(type(item["human_label"]) is str
                and item["human_label"] in LABELS,
                "invalid_external_human_label")
        require(type(prediction) is str and prediction in LABELS,
                "invalid_neural_classification")
        matrix[item["human_label"]][prediction] += 1
    support_truth = sum(matrix["entailment"].values())
    non_support = sum(sum(matrix[gold].values()) for gold in ("neutral", "contradiction"))
    require(support_truth == PER_CLASS and non_support == 2 * PER_CLASS,
            "human_label_distribution_changed")
    exact_correct = sum(matrix[x][x] for x in LABELS)
    false_support = matrix["neutral"]["entailment"] + matrix["contradiction"]["entailment"]
    assert non_support > 0
    metrics = {}
    for label in LABELS:
        tp = matrix[label][label]
        gold_count = sum(matrix[label].values())
        predicted_count = sum(matrix[x][label] for x in LABELS)
        metrics[label] = {
            "correct": tp,
            "human_labeled": gold_count,
            "model_predicted": predicted_count,
            "recall_on_subset": round(tp / gold_count, 6) if gold_count else None,
            "precision_on_subset": (
                round(tp / predicted_count, 6) if predicted_count else None
            ),
        }
    return {
        "subset_cases": len(selected),
        "human_label_counts": {
            label: sum(matrix[label].values()) for label in LABELS
        },
        "model_prediction_counts": {
            label: sum(matrix[x][label] for x in LABELS) for label in LABELS
        },
        "confusion_matrix_human_rows_model_columns": matrix,
        "correct_on_fixed_subset": exact_correct,
        "accuracy_on_fixed_subset": round(exact_correct / len(selected), 6),
        "false_entailment_on_human_non_entailment": {
            "false_entailment_count": false_support,
            "human_non_entailment_count": non_support,
            "rate_on_subset": round(false_support / non_support, 6),
            "from_neutral": matrix["neutral"]["entailment"],
            "from_contradiction": matrix["contradiction"]["entailment"],
        },
        "per_class": metrics,
        "population_factual_accuracy_established": False,
        "semantic_model_production_authority_granted": False,
    }


def evaluate_actual_model(model: Any, selected: list[dict[str, Any]]) -> dict[str, Any]:
    predictions = []
    for item in selected:
        try:
            _validated_pair(item["premise"], item["hypothesis"])
            response = model.predict(item["premise"], item["hypothesis"])
        except Exception:
            raise ExternalEvaluationError("neural_model_inference_failed") from None
        require(type(response) is dict
                and response.get("predicted_relation") in EXPECTED_LABELS
                and response.get("not_a_truth_probability") is True
                and response.get("not_authorized_to_support_claim") is True,
                "neural_output_not_non_authoritative")
        scores = response.get("uncalibrated_model_scores")
        require(type(scores) is dict and set(scores) == set(EXPECTED_LABELS)
                and all(type(scores[x]) in (int, float) and not isinstance(scores[x], bool)
                        and 0 <= scores[x] <= 1 for x in EXPECTED_LABELS)
                and abs(sum(scores.values()) - 1.0) < 0.00001,
                "model_score_contract_invalid")
        predictions.append(response["predicted_relation"])
    return score_predictions(selected, predictions)


def run_live(*, cache_dir: Path) -> dict[str, Any]:
    try:
        from huggingface_hub import hf_hub_download
        location = hf_hub_download(
            repo_id=DATASET_REPO, repo_type="dataset",
            filename=DATASET_FILE, revision=DATASET_REVISION,
            cache_dir=str(cache_dir),
        )
    except Exception:
        raise ExternalEvaluationError("dataset_download_unavailable") from None
    cases = select_fixed_balanced_subset(load_external_human_labeled_rows(Path(location)))
    model = load_reviewed_model(cache_dir=cache_dir, live=True)
    scores = evaluate_actual_model(model, cases)
    return {
        "milestone": "step239_real_external_human_annotated_nli",
        "dataset_repository": DATASET_REPO,
        "dataset_revision": DATASET_REVISION,
        "dataset_validation_file_sha256": DATASET_SHA256,
        "dataset_license": DATASET_LICENSE,
        "annotation_origin": "external_SNLI_crowdsourced_not_reaudited_by_this_project",
        "validation_split_rows": EXPECTED_DATASET_ROWS,
        "sampling": "first_40_eligible_per_label_in_original_validation_row_order_not_random",
        "pretrained_model": MODEL_REPO,
        "model_revision": MODEL_REVISION,
        "quantized_onnx_sha256": ONNX_SHA256,
        "genuine_neural_inference": True,
        "externally_created_human_reference_labels": True,
        "independently_reaudited_labels": False,
        "model_trained_on_snli_family": True,
        "out_of_distribution_accuracy_established": False,
        "original_source_authorship_verified": False,
        "domain_factual_accuracy_established": False,
        "confidence_scores_calibrated": False,
        "neural_production_support_authority": False,
        "public_deployment": False,
        "metrics": scores,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--cache-dir", type=Path, default=Path("/tmp/arl-step239-snli"))
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("external human-labeled dataset/model download disabled; --live required")
    try:
        print(json.dumps(run_live(cache_dir=args.cache_dir), sort_keys=True))
        return 0
    except Exception:
        print("Step 239 external annotated neural NLI evaluation failed; no factual authority granted")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
