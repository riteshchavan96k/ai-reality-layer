"""Step237 research-only NLI contracts (no model downloads in normal tests)."""

from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path

import pytest

from backend.app.evaluation.step236_semantic_baseline import load_candidates
from backend.app.evaluation import step237_nli_shadow as shadow


class FakeResearchModel:
    """Only a test double; not asserted to be a neural model."""
    def __init__(self):
        self.calls = []

    def predict(self, premise, hypothesis):
        self.calls.append((premise, hypothesis))
        return {
            "predicted_relation": "neutral",
            "uncalibrated_model_scores": {
                "contradiction": 0.1, "entailment": 0.2, "neutral": 0.7
            },
            "not_a_truth_probability": True,
            "not_authorized_to_support_claim": True,
        }


def test_shadow_module_import_cannot_perform_model_network_or_modify_api():
    assert shadow.MODEL_REPO == "cross-encoder/nli-MiniLM2-L6-H768"
    assert shadow.MODEL_REVISION == "b95119c"
    assert shadow.ALLOWED_ASSETS == (
        "onnx/model_quint8_avx2.onnx", "tokenizer.json", "config.json"
    )
    assert len(shadow.ONNX_SHA256) == 64
    from backend.app.models.catalog import MODEL_CATALOG
    assert list(MODEL_CATALOG) == ["mock-model"]


def test_shadow_required_explicit_live_optin_before_hub_import(tmp_path):
    with pytest.raises(shadow.ShadowNLIError, match="live_model_acquisition_not_authorized"):
        shadow.load_reviewed_model(cache_dir=tmp_path, live=False)


def test_shadow_no_download_by_default(capsys):
    with pytest.raises(SystemExit):
        shadow.main([])
    assert "no implicit model download" in capsys.readouterr().err


@pytest.mark.parametrize("invalid", [
    {"id2label": {"0": "entailment", "1": "contradiction", "2": "neutral"}, "model_type": "roberta"},
    {"id2label": {"0": "contradiction", "1": "entailment"}, "model_type": "roberta"},
    {"id2label": {"0": "contradiction", "1": "entailment", "2": "neutral"}, "model_type": "bert"},
    {"id2label": ["contradiction", "entailment", "neutral"], "model_type": "roberta"},
    {"id2label": {"0": "contradiction", "1": "entailment", "2": "neutral", "3": "other"}, "model_type": "roberta"},
    None,
])
def test_label_and_architecture_swap_cannot_be_accepted(invalid):
    with pytest.raises(shadow.ShadowNLIError):
        shadow._validate_label_config(invalid)


@pytest.mark.parametrize("scores", [
    [], [[1, 2]], [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]],
    [[float("nan"), 0.2, 0.3]],
    [[float("inf"), 0.2, 0.3]],
    [[None, 0.2, 0.3]],
    [[True, 0.2, 0.3]],
])
def test_invalid_logits_are_rejected(scores):
    with pytest.raises(shadow.ShadowNLIError):
        shadow._normalized_logits(scores)


def test_valid_three_label_logits_do_not_claim_truth():
    label, probabilities = shadow._normalized_logits([[0.5, 1.2, -1.0]])
    assert label == "entailment"
    assert set(probabilities) == {"contradiction", "entailment", "neutral"}
    assert sum(probabilities.values()) == pytest.approx(1, abs=0.000003)
    assert probabilities["entailment"] > probabilities["contradiction"]
    assert all(math.isfinite(x) for x in probabilities.values())


@pytest.mark.parametrize("premise,hypothesis", [
    ("", "valid claim"),
    ("valid premise", ""),
    (" " * 4, "valid claim"),
    ("good", "x" * 501),
    ("x" * 501, "good"),
    ("\x00", "good"),
    ("good", "contains\rreturn"),
    (2, "good"),
])
def test_unbounded_or_bad_model_input_fails_closed(premise, hypothesis):
    with pytest.raises(shadow.ShadowNLIError):
        shadow._validated_pair(premise, hypothesis)


def test_known_weights_digest_rejects_tampering(tmp_path, monkeypatch):
    p = tmp_path / "model_quint8_avx2.onnx"
    p.write_bytes(b"valid-for-unit-test-only")
    with pytest.raises(shadow.ShadowNLIError, match="model_weights_digest_mismatch"):
        shadow._hash_verified_weights(p)
    checksum = sha256(p.read_bytes()).hexdigest()
    monkeypatch.setattr(shadow, "ONNX_SHA256", checksum)
    assert shadow._hash_verified_weights(p) == checksum
    p.write_bytes(b"modified-for-test")
    with pytest.raises(shadow.ShadowNLIError, match="model_weights_digest_mismatch"):
        shadow._hash_verified_weights(p)


def test_shadow_compares_all_20_actual_frozen_pairs_without_any_authority():
    model = FakeResearchModel()
    manifest = load_candidates()
    report = shadow.evaluate_shadow(model, manifest)
    assert report["candidate_count"] == 20
    assert len(model.calls) == 20
    assert model.calls[0] == (
        manifest["cases"][0]["evidence_excerpt"], manifest["cases"][0]["claim"]
    )
    assert report["model_predictions_can_authorize_claim_support"] is False
    assert report["original_publisher_bytes_verified_for_this_dataset"] is False
    assert report["independent_human_labels_verified"] is False
    assert report["unverified_human_accuracy"] is None
    assert report["production_api_changed"] is False
    assert report["text_baseline_counts"] == {
        "abstain": 14, "bounded_alignment": 3, "bounded_contradiction": 3
    }
    assert report["neural_label_counts"] == {"neutral": 20}
    assert set(row["neural_shadow_prediction"] for row in report["results"]) == {"neutral"}
    assert all(row["neural_prediction_authorized"] is False for row in report["results"])
    assert "model_input" not in json.dumps(report)


@pytest.mark.parametrize("bad", [
    {"predicted_relation": "supported", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": True},
    {"predicted_relation": "entailment", "not_a_truth_probability": True,
     "not_authorized_to_support_claim": False},
    {"predicted_relation": "entailment", "not_authorized_to_support_claim": True},
    None,
])
def test_neural_shadow_result_cannot_sneak_in_supported_claim(bad):
    class Unsafe:
        def predict(self, *args):
            return bad
    with pytest.raises(shadow.ShadowNLIError, match="invalid_shadow_prediction"):
        shadow.evaluate_shadow(Unsafe(), load_candidates())


def test_model_call_requires_actual_authentication_of_candidate_dataset():
    original = load_candidates()
    forged = deepcopy(original)
    forged["independent_human_labels_verified"] = True
    with pytest.raises(shadow.ShadowNLIError, match="invalid_shadow_candidate_set"):
        shadow.evaluate_shadow(FakeResearchModel(), forged)


def test_cli_with_injected_model_only_emits_safe_audit(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(shadow, "load_reviewed_model", lambda **kw: FakeResearchModel())
    assert shadow.main(["--live", "--cache-dir", str(tmp_path), "--summary-only"]) == 0
    audit = json.loads(capsys.readouterr().out)
    assert audit["candidate_count"] == 20
    assert audit["neural_model_executed"] is True  # mocked CLI unit path, not live proof
    assert audit["model_predictions_can_authorize_claim_support"] is False
    assert "results" not in audit


def test_failed_download_is_sanitized_without_leak(monkeypatch, capsys):
    def network_exception(**kwargs):
        raise shadow.ShadowNLIError("reviewed_model_download_unavailable")
    monkeypatch.setattr(shadow, "load_reviewed_model", network_exception)
    assert shadow.main(["--live"]) == 1
    assert "failed" in capsys.readouterr().out
