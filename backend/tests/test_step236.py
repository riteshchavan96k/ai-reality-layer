"""Step 236: real deterministic parser baseline plus untrusted blind-review tooling.

These tests do not invent human reviewers or claim real-world semantic accuracy.
All source excerpts are developer-origin, including forged text deliberately
associated with genuine publisher URL candidates.
"""

from copy import deepcopy
import json

import pytest

from backend.app.evaluation.step236_semantic_baseline import (
    CASE_IDS,
    DATASET_ID,
    FROZEN_DATASET_SHA256,
    SemanticEvaluationError,
    baseline_prediction,
    baseline_report,
    blind_review_packet,
    conditional_review_comparison,
    load_candidates,
    main,
)


def candidate_by_id(manifest, id):
    return next(item for item in manifest["cases"] if item["id"] == id)


def reviewer_file(manifest, *, label="neutral"):
    baseline = baseline_report(manifest)
    return {
        "schema_version": "1.0",
        "dataset_sha256": baseline["dataset_sha256"],
        "review_identity_audit_status": "not_independently_verified",
        "annotations": [
            {"case_id": case_id, "reviewer_id": reviewer, "label": label}
            for case_id in sorted(CASE_IDS)
            for reviewer in ("candidate-reviewer-A", "candidate-reviewer-B")
        ],
    }


def test_versioned_manifest_contains_twenty_unreviewed_pairs_without_gold_or_outputs():
    dataset = load_candidates()
    assert dataset["dataset_id"] == DATASET_ID
    assert len(dataset["cases"]) == 20
    assert {x["id"] for x in dataset["cases"]} == CASE_IDS
    assert dataset["independent_human_labels_verified"] is False
    assert dataset["evidence_publisher_capture_verified"] is False
    assert dataset["representative_population"] is False
    assert sum(x["id"].startswith("s232-") for x in dataset["cases"]) == 12
    assert sum(x["id"].startswith("syn-") for x in dataset["cases"]) == 8
    for case in dataset["cases"]:
        assert not {"expected", "gold", "label", "prediction", "source_capture_sha256"} & case.keys()
        assert case["evidence_origin"] in {
            "synthetic_fictional_exercise",
            "developer_authored_pair_using_real_publisher_url_not_capture",
        }


def test_actual_atomic_parser_baseline_exposes_limit_and_source_spoof_risk():
    manifest = load_candidates()
    prediction = lambda case_id: baseline_prediction(candidate_by_id(manifest, case_id))
    assert prediction("s232-python-direct-supported") == "bounded_alignment"
    assert prediction("s232-python-supported-but-outside-grammar") == "abstain"
    assert prediction("s232-python-direct-negation") == "bounded_contradiction"
    assert prediction("syn-service-paraphrase") == "abstain"
    assert prediction("syn-service-negation") == "bounded_contradiction"
    assert prediction("syn-date-different") == "bounded_contradiction"
    # Text-only relation can align a developer-forged excerpt: not truth.
    assert prediction("s232-python-forged-release-date") == "bounded_alignment"
    # An excerpt falsely attributed to IANA also aligns textually; no source proof.
    assert prediction("s232-iana-python-text-misattribution") == "bounded_alignment"
    report = baseline_report(manifest)
    assert report["candidate_count"] == 20
    assert report["prediction_counts"] == {
        "abstain": 14, "bounded_alignment": 3, "bounded_contradiction": 3
    }
    assert report["independent_human_labels_verified"] is False
    assert report["population_accuracy_established"] is False
    assert report["semantic_nli_model_executed"] is False
    assert report["dataset_sha256"] == FROZEN_DATASET_SHA256


def test_blind_packet_excludes_predictions_prior_gold_and_secret_metadata():
    corpus = load_candidates()
    packet = blind_review_packet(corpus)
    assert packet["review_status"] == "not_collected"
    assert packet["independent_human_labels_verified"] is False
    assert packet["dataset_sha256"] == baseline_report(corpus)["dataset_sha256"]
    assert len(packet["cases"]) == 20
    serialized = json.dumps(packet).lower()
    assert "bounded_alignment" not in serialized
    assert "bounded_contradiction" not in serialized
    assert "supports_claim" not in serialized
    assert "expected_decision" not in serialized
    assert "model_prediction" not in serialized
    assert "publisher_capture_verified" not in serialized


@pytest.mark.parametrize("edit", [
    lambda x: x.update({"independent_human_labels_verified": True}),
    lambda x: x.update({"evidence_publisher_capture_verified": True}),
    lambda x: x.update({"representative_population": True}),
    lambda x: x.update({"label_provenance": "independent_reviewer_approved"}),
    lambda x: x["cases"].pop(),
    lambda x: x["cases"][0].update({"id": x["cases"][1]["id"]}),
    lambda x: x["cases"][0].update({"id": "unknown-case"}),
    lambda x: x["cases"][0].update({"source_ref": "http://localhost/private"}),
    lambda x: x["cases"][0].update({"evidence_origin": "synthetic_fictional_exercise"}),
    lambda x: x["cases"][0].update({"gold": "entails"}),
    lambda x: x["cases"][0].update({"prediction": "bounded_alignment"}),
    lambda x: x["cases"][0].update({"claim": "X" * 501}),
    lambda x: x.update({"neural_nli_accuracy": 1.0}),
])
def test_manifest_rejects_tampering_provenance_gold_and_bad_fields(tmp_path, edit):
    raw = deepcopy(load_candidates())
    edit(raw)
    path = tmp_path / "untrusted.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SemanticEvaluationError):
        load_candidates(path)


def test_empty_review_does_not_produce_accuracy_or_fabricate_labels():
    manifest = load_candidates()
    review = {
        "schema_version": "1.0",
        "dataset_sha256": baseline_report(manifest)["dataset_sha256"],
        "review_identity_audit_status": "not_independently_verified",
        "annotations": [],
    }
    result = conditional_review_comparison(manifest, review)
    assert result["status"] == "incomplete"
    assert result["missing_review_cases"] == 20
    assert result["conditional_counts"] is None
    assert result["independent_human_labels_verified"] is False


def test_one_reviewer_per_case_not_accepted_as_consensus():
    manifest = load_candidates()
    review = reviewer_file(manifest)
    review["annotations"] = review["annotations"][::2]
    result = conditional_review_comparison(manifest, review)
    assert result["status"] == "incomplete"
    assert result["complete_two_review_cases"] == 0
    assert result["conditional_counts"] is None


def test_two_disagreeing_reviewers_do_not_get_scored():
    manifest = load_candidates()
    review = reviewer_file(manifest)
    review["annotations"][0]["label"] = "entails"
    result = conditional_review_comparison(manifest, review)
    assert result["status"] == "disputed"
    assert result["disputed_cases"] == 1
    assert result["conditional_counts"] is None


def test_user_submitted_consensus_is_conditional_not_verified_external_review():
    manifest = load_candidates()
    review = reviewer_file(manifest, label="neutral")
    result = conditional_review_comparison(manifest, review)
    assert result["status"] == "conditional_consensus_unverified_reviewer_identities"
    assert result["independent_human_labels_verified"] is False
    assert result["reviewer_identity_authentication"] == "not_independently_verified"
    assert result["population_accuracy_established"] is False
    assert result["conditional_counts"]["possible_false_support"] == 3
    assert result["conditional_counts"]["bounded_alignment_on_submitted_entailment"] == 0
    assert result["conditional_counts"]["submitted_entailment_count"] == 0
    assert result["conditional_counts"]["reviewed_case_count"] == 20
    assert result["conditional_counts"]["incorrect_contradictions"] == 3


def test_conditional_counts_detect_false_support_and_partial_coverage():
    corpus = load_candidates()
    review = reviewer_file(corpus)
    target_id = "s232-python-direct-supported"
    for record in review["annotations"]:
        if record["case_id"] == target_id:
            record["label"] = "entails"
    scored = conditional_review_comparison(corpus, review)["conditional_counts"]
    assert scored["bounded_alignment_on_submitted_entailment"] == 1
    assert scored["submitted_entailment_count"] == 1
    assert scored["possible_false_support"] == 2
    assert scored["abstained"] == 14


@pytest.mark.parametrize("edit", [
    lambda r: r.update({"dataset_sha256": "a" * 64}),
    lambda r: r.update({"review_identity_audit_status": "verified_by_ai"}),
    lambda r: r.update({"independent_human_labels_verified": True}),
    lambda r: r["annotations"][0].update({"case_id": "unknown"}),
    lambda r: r["annotations"][0].update({"label": "verified_true"}),
    lambda r: r["annotations"][0].update({"reviewer_id": "developer/model"}),
    lambda r: r["annotations"][1].update({"reviewer_id": "candidate-reviewer-A"}),
    lambda r: r["annotations"].append(deepcopy(r["annotations"][0])),
    lambda r: r["annotations"][0].update({"raw_source_page": "secret"}),
])
def test_untrusted_review_input_is_strictly_validated(edit):
    manifest = load_candidates()
    review = reviewer_file(manifest)
    edit(review)
    with pytest.raises(SemanticEvaluationError):
        conditional_review_comparison(manifest, review)


def test_cli_summary_and_blind_export_are_deterministic(tmp_path, capsys):
    first = main(["--summary-only"])
    first_value = json.loads(capsys.readouterr().out)
    destination = tmp_path / "blind_packet.json"
    second = main(["--summary-only", "--blind-packet", str(destination)])
    second_value = json.loads(capsys.readouterr().out)
    packet = json.loads(destination.read_text(encoding="utf-8"))
    assert first == second == 0
    assert first_value == second_value
    assert "results" not in first_value
    assert packet["dataset_sha256"] == first_value["dataset_sha256"]


def test_cli_rejects_bad_review_without_source_or_token_leak(tmp_path, capsys):
    path = tmp_path / "invalid_review.json"
    path.write_text(json.dumps({"unexpected": "private-credential-and-secret"}), encoding="utf-8")
    assert main(["--summary-only", "--review-file", str(path)]) == 1
    stdout = capsys.readouterr().out
    assert "private-credential-and-secret" not in stdout
    assert "invalid" in stdout


def test_review_manifest_sha_changes_with_evidence_change_and_prevents_replay(tmp_path):
    corpus = load_candidates()
    review = reviewer_file(corpus)
    mutated = deepcopy(corpus)
    mutated["cases"][0]["evidence_excerpt"] = "Another developer-authored statement."
    path = tmp_path / "updated.json"
    path.write_text(json.dumps(mutated), encoding="utf-8")
    # The reviewed-case corpus cannot silently drift under the same dataset ID.
    with pytest.raises(SemanticEvaluationError):
        load_candidates(path)
    # A stale reviewer manifest cannot be silently treated as applicable to
    # a revised candidate collection: a new version and separate reviews are required.
    assert review["dataset_sha256"] == FROZEN_DATASET_SHA256


def test_bad_corpus_json_and_large_file_refused(tmp_path):
    broken = tmp_path / "bad.json"
    broken.write_bytes(b"{not valid json")
    with pytest.raises(SemanticEvaluationError):
        load_candidates(broken)
    broken.write_bytes(b"x" * (128 * 1024 + 1))
    with pytest.raises(SemanticEvaluationError):
        load_candidates(broken)
