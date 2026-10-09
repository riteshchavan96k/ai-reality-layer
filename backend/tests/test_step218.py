"""Step 218: truthful publisher-anchored evaluation with clearly synthetic attacks."""

import json
from collections import Counter
from pathlib import Path

import pytest

from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.evaluation import official_source_quality_benchmark as bench


def _variant(tmp_path, edit):
    raw = json.loads(bench.DATASET_PATH.read_text(encoding="utf-8"))
    edit(raw)
    target = tmp_path / "variant.json"
    target.write_text(json.dumps(raw), encoding="utf-8")
    return target


def test_eight_real_publisher_urls_and_historical_release_annotations():
    dataset = bench.load_dataset()
    assert len(dataset["anchors"]) == 8
    assert len(dataset["cases"]) == 48
    assert len({a["uri"] for a in dataset["anchors"]}) == 8
    assert all(a["uri"].startswith("https://") for a in dataset["anchors"])
    assert all(a["reviewed_by"] == "assistant_source_review_not_independent_human" for a in dataset["anchors"])
    assert dataset["replay_time_is_synthetic"] is True


def test_every_source_is_replayed_once_per_scenario():
    d = bench.load_dataset()
    seen = Counter((x["anchor_id"], x["scenario"]) for x in d["cases"])
    assert len(seen) == 48
    assert set(c for _, c in seen) == set(bench.SCENARIOS)
    assert all(v == 1 for v in seen.values())


def test_benchmark_runs_current_reality_state_with_honest_metrics():
    report = bench.run_baseline()
    assert report["case_count"] == 48
    assert report["source_count"] == 8
    assert report["counts"]["should_abstain"] == 40
    assert report["counts"]["safe_to_support"] == 8
    assert report["counts"]["wrong_topic_cases"] == 8
    assert report["counts"]["conflict_expected"] == 8
    assert sum(s["cases"] for s in report["scenarios"].values()) == 48
    assert len(report["cases"]) == 48
    assert report["metrics"]["false_support_rate"] == pytest.approx(
        report["counts"]["false_supports"] / 40
    )
    assert report["metrics"]["irrelevant_evidence_false_support_rate"] == pytest.approx(
        report["counts"]["wrong_topic_false_supports"] / 8
    )
    assert all(item["source_content_integrity_authenticated"] is False for item in report["cases"])


def test_product_inputs_have_no_oracle_metadata(monkeypatch):
    original = bench.build_reality_state_from_evidence
    seen = []

    def intercept(task, documents, **kwargs):
        assert isinstance(task, str)
        assert "oracle" not in kwargs and "label_authority" not in kwargs
        assert all("oracle" not in document for document in documents)
        assert all("should_abstain" not in document for document in documents)
        seen.append(task)
        return original(task, documents, **kwargs)

    monkeypatch.setattr(bench, "build_reality_state_from_evidence", intercept)
    bench.run_baseline(include_cases=False)
    assert len(seen) == 48


def test_original_publisher_case_has_authored_summary_and_real_uri_only():
    d = bench.load_dataset()
    anchor = d["anchors"][0]
    case = next(x for x in d["cases"] if x["anchor_id"] == anchor["id"] and x["scenario"] == "publisher_relevant")
    doc_input = bench._build_input(case, anchor, d["anchors"], d)
    assert len(doc_input["documents"]) == 1
    assert doc_input["documents"][0]["uri"] == anchor["uri"]
    assert doc_input["documents"][0]["content"] == anchor["statement"]
    assert doc_input["freshness_max_age_seconds"] == 3600
    EvidenceRealityStateRequest.model_validate(doc_input)


def test_real_url_content_tampering_is_explicit_and_not_confused_with_official_content():
    d = bench.load_dataset()
    anchor = d["anchors"][0]
    case = next(x for x in d["cases"] if x["anchor_id"] == anchor["id"] and x["scenario"] == "url_content_tampering")
    item = bench._build_input(case, anchor, d["anchors"], d)["documents"][0]
    assert item["uri"] == anchor["uri"]
    assert item["content"] == "Not " + anchor["statement"]
    assert item["content"] != anchor["statement"]


def test_irrelevant_official_evidence_uses_different_real_publisher_uri():
    d = bench.load_dataset()
    anchor = d["anchors"][0]
    case = next(x for x in d["cases"] if x["anchor_id"] == anchor["id"] and x["scenario"] == "irrelevant_official_page")
    payload = bench._build_input(case, anchor, d["anchors"], d)
    assert payload["documents"][0]["uri"] == d["anchors"][1]["uri"]
    assert anchor["entity"] in payload["task"]
    assert d["anchors"][1]["entity"] in payload["documents"][0]["content"]


def test_conflicting_second_document_is_clearly_marked_as_fabricated():
    d = bench.load_dataset()
    anchor = d["anchors"][0]
    case = next(x for x in d["cases"] if x["anchor_id"] == anchor["id"] and x["scenario"] == "explicit_synthetic_conflict")
    docs = bench._build_input(case, anchor, d["anchors"], d)["documents"]
    assert len(docs) == 2
    assert docs[0]["uri"] == anchor["uri"]
    assert docs[1]["uri"].startswith("https://fixtures.example.test/")
    assert docs[1]["title"].startswith("SYNTHETIC")
    assert docs[1]["content"].startswith("Not ")


def test_observation_replay_and_missing_freshness_are_different():
    d = bench.load_dataset()
    anchor = d["anchors"][0]
    choices = {case["scenario"]: case for case in d["cases"] if case["anchor_id"] == anchor["id"]}
    stale = bench._build_input(choices["stale_source_observation"], anchor, d["anchors"], d)
    missing = bench._build_input(choices["no_declared_freshness_policy"], anchor, d["anchors"], d)
    assert stale["documents"][0]["observed_at"] == d["old_observation_utc"]
    assert stale["freshness_max_age_seconds"] == 3600
    assert missing["documents"][0]["observed_at"] == d["recent_observation_utc"]
    assert missing["freshness_max_age_seconds"] is None


def test_scorecard_contains_no_false_real_world_accuracy_claim():
    report = bench.run_baseline(include_cases=False)
    assert report["corpus_type"] == "real-official-source-anchored-plus-synthetic-adversarial-inputs"
    assert any("not blind independently" in x for x in report["limitations"])
    assert any("not original publisher text captures" in x for x in report["limitations"])
    assert any("does not fetch" in x for x in report["limitations"])
    assert "cases" not in report
    for score in report["metrics"].values():
        assert score is None or 0 <= score <= 1


@pytest.mark.parametrize("edit,match", [
    (lambda d: d["anchors"].append(d["anchors"][0]), "exactly eight anchors"),
    (lambda d: d["cases"].append(d["cases"][0]), "exactly 48 evaluation cases"),
    (lambda d: d["cases"][0].update(id=d["cases"][1]["id"]), "unique case IDs"),
    (lambda d: d["anchors"][0].update(uri="https://fixtures.example.test/fake"), "official publisher URL"),
    (lambda d: d["anchors"][0].update(reviewed_by="independent human"), "provenance review disclosure"),
    (lambda d: d["cases"][0]["oracle"].update(should_abstain=True), "inconsistent review label"),
    (lambda d: d["cases"][0]["oracle"].pop("label_authority"), "missing review-limit disclosure"),
    (lambda d: d.update(replay_time_is_synthetic=False), "synthetic time disclosure"),
])
def test_dataset_corruption_is_rejected_loudly(tmp_path, edit, match):
    with pytest.raises(ValueError, match=match):
        bench.load_dataset(_variant(tmp_path, edit))


def test_changed_oracle_reason_does_not_affect_replayed_product_predictions(tmp_path):
    original = bench.run_baseline()
    changed = bench.run_baseline(
        _variant(tmp_path, lambda d: d["cases"][0]["oracle"].update(reason="New reviewer explanation."))
    )
    assert [(x["id"], x["predicted_status"]) for x in original["cases"]] == [
        (x["id"], x["predicted_status"]) for x in changed["cases"]
    ]


def test_runner_never_attempts_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("offline benchmark must not fetch network pages")

    monkeypatch.setattr("urllib.request.urlopen", blocked)
    assert bench.run_baseline(include_cases=False)["case_count"] == 48


def test_cli_can_write_summary_json_without_fabricated_success(tmp_path, capsys):
    destination = tmp_path / "benchmark.json"
    assert bench.main(["--summary-only", "--output", str(destination)]) == 0
    printed = json.loads(capsys.readouterr().out)
    saved = json.loads(destination.read_text(encoding="utf-8"))
    assert saved == printed
    assert saved["case_count"] == 48
    assert "false_supports" in saved["counts"]


def test_committed_official_source_scorecard_matches_actual_product_replay():
    # A regression that changes product predictions MUST update the observed
    # scorecard explicitly; never leave convenient but stale numbers behind.
    baseline = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "STEP_218_BASELINE.json"
    )
    recorded = json.loads(baseline.read_text(encoding="utf-8"))
    replayed = bench.run_baseline(include_cases=False)
    assert recorded == replayed


def test_metrics_are_derived_from_denominators_not_arbitrary_scores():
    assert bench._ratio(1, 2) == .5
    assert bench._ratio(0, 0) is None
    assert bench._ratio(8, 8) == 1.0
