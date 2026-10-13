"""Step239 contract tests: external human-labeled NLI scorecard and no authority.

These use synthetic *unit-test doubles*, never misrepresented as actual
Stanford human labels. Dedicated CI runs real Stanford validation and ONNX.
"""

from copy import deepcopy
from hashlib import sha256
import json

import pytest

from backend.app.evaluation import step239_external_nli_quality as s


def sample_rows(n=40):
    rows = []
    for i in range(n):
        for code in (0, 1, 2):
            rows.append({
                "premise": f"Test-only premise number {i} in group {code}.",
                "hypothesis": f"Test-only hypothesis number {i} in group {code}.",
                "label": code,
            })
    return rows


def selected():
    return s.select_fixed_balanced_subset(sample_rows())


def perfect_predictions(cases):
    return [row["human_label"] for row in cases]


class FakeModel:
    def __init__(self, predict_as=None):
        self.calls = []
        self.predict_as = predict_as

    def predict(self, premise, hypothesis):
        self.calls.append((premise, hypothesis))
        label = self.predict_as or "neutral"
        return {
            "predicted_relation": label,
            "uncalibrated_model_scores": {
                "entailment": .8 if label == "entailment" else .1,
                "neutral": .8 if label == "neutral" else .1,
                "contradiction": .8 if label == "contradiction" else .1,
            },
            "not_a_truth_probability": True,
            "not_authorized_to_support_claim": True,
        }


def test_immutable_external_dataset_contract_and_correct_semantic_labels():
    assert s.DATASET_REPO == "stanfordnlp/snli"
    assert s.DATASET_FILE == "plain_text/validation-00000-of-00001.parquet"
    assert len(s.DATASET_SHA256) == 64
    assert s.DATASET_LICENSE == "CC-BY-SA-4.0"
    assert s.LABEL_IDS == {0: "entailment", 1: "neutral", 2: "contradiction"}
    assert s.PER_CLASS == 40 and s.EXPECTED_EVALUATED == 120


def test_selects_first_balanced_rows_in_dataset_order_without_fake_labels():
    rows = sample_rows(50)
    cases = s.select_fixed_balanced_subset(rows)
    assert len(cases) == 120
    assert [row["human_label"] for row in cases[:3]] == [
        "entailment", "neutral", "contradiction"
    ]
    assert cases[0]["row_index"] == 0
    assert cases[-1]["row_index"] == 119
    assert [row["human_label"] for row in cases].count("entailment") == 40
    assert [row["human_label"] for row in cases].count("neutral") == 40
    assert [row["human_label"] for row in cases].count("contradiction") == 40


def test_unlabeled_rows_explicitly_skipped():
    rows = [{"premise": "Undecided label", "hypothesis": "Unreviewed hypothesis", "label": -1}]
    rows += sample_rows()
    cases = s.select_fixed_balanced_subset(rows)
    assert len(cases) == 120
    assert cases[0]["row_index"] == 1


def test_bounded_invalid_pairs_excluded_no_truncated_text_accepted():
    rows = [{"premise": "a" * 501, "hypothesis": "test", "label": 0},
            {"premise": " bad leading space", "hypothesis": "test", "label": 1},
            {"premise": "null\x00", "hypothesis": "test", "label": 2}]
    rows += sample_rows()
    cases = s.select_fixed_balanced_subset(rows)
    assert len(cases) == 120
    assert min(x["row_index"] for x in cases) == 3


@pytest.mark.parametrize("bad", [
    {"premise": "P", "hypothesis": "H", "label": True},
    {"premise": "P", "hypothesis": "H", "label": "0"},
    {"premise": "P", "hypothesis": "H", "label": 3},
    {"premise": "P", "hypothesis": "H", "label": None},
    {"premise": "P", "hypothesis": "H", "label": 0, "gold": "entailment"},
    ["P", "H", 0],
])
def test_invalid_labels_or_unexpected_schema_fail_closed(bad):
    with pytest.raises(s.ExternalEvaluationError):
        s.select_fixed_balanced_subset([bad] + sample_rows())


@pytest.mark.parametrize("count", [0, -1, 41, 1.0, True])
def test_invalid_sampling_quota_fails_closed(count):
    with pytest.raises(s.ExternalEvaluationError, match="bad_sample_size"):
        s.select_fixed_balanced_subset(sample_rows(), per_label=count)


def test_insufficient_human_label_counts_are_not_silently_scaled():
    with pytest.raises(s.ExternalEvaluationError, match="insufficient_balanced_labeled_cases"):
        s.select_fixed_balanced_subset(sample_rows(3))


def test_repeated_selected_pair_cannot_inflate_denominator():
    rows = sample_rows()
    rows[3] = dict(rows[0])
    with pytest.raises(s.ExternalEvaluationError, match="duplicate_selected_semantic_pair"):
        s.select_fixed_balanced_subset(rows)


def test_perfect_predictions_on_fake_unit_data_show_exact_denominators():
    cases = selected()
    report = s.score_predictions(cases, perfect_predictions(cases))
    assert report["correct_on_fixed_subset"] == 120
    assert report["accuracy_on_fixed_subset"] == 1
    assert report["false_entailment_on_human_non_entailment"] == {
        "false_entailment_count": 0, "human_non_entailment_count": 80,
        "rate_on_subset": 0, "from_neutral": 0, "from_contradiction": 0
    }
    for label in s.LABELS:
        assert report["per_class"][label]["correct"] == 40
        assert report["per_class"][label]["recall_on_subset"] == 1
        assert report["per_class"][label]["precision_on_subset"] == 1
    assert report["semantic_model_production_authority_granted"] is False
    assert report["population_factual_accuracy_established"] is False


def test_all_entailment_predictions_report_forty_true_and_eighty_false_support():
    cases = selected()
    report = s.score_predictions(cases, ["entailment"] * 120)
    assert report["accuracy_on_fixed_subset"] == pytest.approx(1/3, abs=1e-6)
    assert report["correct_on_fixed_subset"] == 40
    assert report["false_entailment_on_human_non_entailment"]["false_entailment_count"] == 80
    assert report["false_entailment_on_human_non_entailment"]["rate_on_subset"] == 1
    assert report["false_entailment_on_human_non_entailment"]["from_neutral"] == 40
    assert report["false_entailment_on_human_non_entailment"]["from_contradiction"] == 40
    assert report["per_class"]["neutral"]["precision_on_subset"] is None
    assert report["per_class"]["contradiction"]["recall_on_subset"] == 0


def test_partial_wrong_entailment_count_exactly_measured():
    cases = selected()
    predictions = perfect_predictions(cases)
    predictions[1] = "entailment"   # human neutral
    predictions[2] = "entailment"   # human contradicted
    report = s.score_predictions(cases, predictions)
    assert report["correct_on_fixed_subset"] == 118
    assert report["false_entailment_on_human_non_entailment"]["false_entailment_count"] == 2
    assert report["false_entailment_on_human_non_entailment"]["rate_on_subset"] == .025


@pytest.mark.parametrize("edit", [
    lambda c, p: p.pop(),
    lambda c, p: p.append("neutral"),
    lambda c, p: p.__setitem__(0, "supported"),
    lambda c, p: p.__setitem__(0, None),
    lambda c, p: c[0].update({"human_label": "verified_fact"}),
    lambda c, p: c[0].update({"row_index": c[1]["row_index"]}),
    lambda c, p: c[0].update({"extra_raw_data": "leak"}),
    lambda c, p: c[0].update({"human_label": "neutral"}),
])
def test_incomplete_or_corrupted_scoring_rejected_where_invariant_broken(edit):
    cases = selected()
    predictions = perfect_predictions(cases)
    edit(cases, predictions)
    with pytest.raises(s.ExternalEvaluationError):
        s.score_predictions(cases, predictions)


def test_fake_model_evaluation_uses_premise_then_hypothesis_and_never_promotes_claim():
    cases = selected()
    model = FakeModel()
    report = s.evaluate_actual_model(model, cases)
    assert len(model.calls) == 120
    assert model.calls[0] == (cases[0]["premise"], cases[0]["hypothesis"])
    assert report["false_entailment_on_human_non_entailment"]["false_entailment_count"] == 0
    assert report["correct_on_fixed_subset"] == 40
    assert report["semantic_model_production_authority_granted"] is False


@pytest.mark.parametrize("bad", [
    None,
    {"predicted_relation": "entailment"},
    {"predicted_relation": "supported", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True},
    {"predicted_relation": "neutral", "not_a_truth_probability": False,
     "not_authorized_to_support_claim": True},
    {"predicted_relation": "neutral", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": False},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True,
     "uncalibrated_model_scores": {
         "entailment": .9, "neutral": .9, "contradiction": .8}},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True,
     "uncalibrated_model_scores": {
         "entailment": float("nan"), "neutral": .1, "contradiction": .9}},
])
def test_malformed_model_outputs_fail_without_quality_score(bad):
    class MisbehavingModel:
        def predict(self, *args):
            return bad
    with pytest.raises(s.ExternalEvaluationError):
        s.evaluate_actual_model(MisbehavingModel(), selected())


def test_check_parquet_sha_rejects_tampered_bytes(tmp_path, monkeypatch):
    file = tmp_path / "external_labels.parquet"
    file.write_bytes(b"fake-dataset-unsafe")
    with pytest.raises(s.ExternalEvaluationError, match="dataset_sha256_mismatch"):
        s.verified_parquet_file(file)
    monkeypatch.setattr(s, "DATASET_SHA256", sha256(file.read_bytes()).hexdigest())
    assert s.verified_parquet_file(file) == file
    file.write_bytes(b"fake-dataset-mutated")
    with pytest.raises(s.ExternalEvaluationError, match="dataset_sha256_mismatch"):
        s.verified_parquet_file(file)


def test_no_network_without_explicit_live_optin(capsys):
    with pytest.raises(SystemExit):
        s.main([])
    assert "--live required" in capsys.readouterr().err


def test_cli_sanitizes_private_dataset_and_inference_errors(monkeypatch, capsys):
    def explode(**kwargs):
        raise RuntimeError("secret-dataset-source-auth-header")
    monkeypatch.setattr(s, "run_live", explode)
    assert s.main(["--live"]) == 1
    message = capsys.readouterr().out
    assert "secret-dataset-source-auth-header" not in message
    assert "no factual authority granted" in message


def test_dataset_download_is_optin_and_expected_repo_file_constant():
    assert s.DATASET_REPO == "stanfordnlp/snli"
    assert s.DATASET_FILE.startswith("plain_text/validation-")
    assert s.EXPECTED_DATASET_ROWS == 10_000


def test_authoritative_apis_are_not_imported_by_benchmark():
    from backend.app.models.catalog import MODEL_CATALOG
    assert list(MODEL_CATALOG) == ["mock-model"]
    assert "original_source_claim_service" not in s.__dict__
