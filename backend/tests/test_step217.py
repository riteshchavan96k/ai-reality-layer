"""Step 217: evaluation integrity, independent labels, and product replay."""

from collections import Counter
import json
from pathlib import Path

import pytest
from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest

from backend.app.evaluation import reality_state_quality_benchmark as bench
from backend.app.main import reality_state_from_evidence


def _altered_fixture(tmp_path, transform):
    fixture = json.loads(bench.DATASET_PATH.read_text(encoding="utf-8"))
    transform(fixture)
    p = tmp_path / "controlled-v1.json"
    p.write_text(json.dumps(fixture), encoding="utf-8")
    return p


def test_all_48_cases_span_eight_entities_and_six_failure_scenarios():
    d = bench.load_dataset()
    assert d["dataset_id"] == "step217-controlled-v1"
    assert len(d["cases"]) == 48
    assert len({x["entity"] for x in d["cases"]}) == 8
    assert Counter(x["scenario"] for x in d["cases"]) == {
        scenario: 8 for scenario in bench.SCENARIOS
    }


def test_dataset_has_independent_oracle_and_no_pretend_live_sources():
    dataset = bench.load_dataset()
    for case in dataset["cases"]:
        assert case["gold"]["world_reference_is_simulated"] is True
        assert case["gold"]["justification"]
        assert case["gold"]["expected_claims"]
        assert all(
            doc["uri"].startswith("https://fixtures.example.test/")
            for doc in case["documents"]
        )


def test_end_to_end_runner_returns_auditable_48_case_metrics():
    report = bench.run_baseline()
    assert report["case_count"] == 48
    assert report["fixture_type"] == "offline-controlled-simulated-oracle"
    assert len(report["cases"]) == 48
    assert report["counts"]["cases"] == 48
    assert report["counts"]["should_abstain"] == 40
    assert report["counts"]["safe_to_support"] == 8
    assert report["counts"]["gold_conflicts"] == 16
    assert sum(x["cases"] for x in report["scenarios"].values()) == 48
    assert report["metrics"]["false_support_rate"] == pytest.approx(
        report["counts"]["false_supports"] / 40
    )
    assert report["metrics"]["conflict_recall"] == pytest.approx(
        report["counts"]["matched_conflicts"] / 16
    )
    assert any("not field-measured factual accuracy" in limitation for limitation in report["limitations"])


def test_step217_historical_pre_entity_gate_scorecard_is_preserved():
    # The original Step 217 scorecard describes the PRE-Step-219 engine.
    # Keep it immutable as an honest before/after comparison. Step 219
    # separately asserts current engine replay against its new scorecard.
    baseline_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "STEP_217_BASELINE.json"
    )
    recorded = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert recorded["dataset_id"] == "step217-controlled-v1"
    assert recorded["case_count"] == 48
    assert recorded["counts"]["false_supports"] == 16
    assert recorded["counts"]["correct_abstentions"] == 24
    assert recorded["metrics"]["false_support_rate"] == 0.4
    assert recorded["metrics"]["safe_abstention_rate"] == 0.6



def test_all_reported_metrics_are_bounded_without_inventing_performance():
    report = bench.run_baseline(include_cases=False)
    assert "cases" not in report
    assert len(report["metrics"]) == 12
    for value in report["metrics"].values():
        assert value is None or 0.0 <= value <= 1.0


def test_case_report_preserves_failures_instead_of_silencing_them():
    report = bench.run_baseline()
    assert [x["id"] for x in report["cases"]] == [
        c["id"] for c in bench.load_dataset()["cases"]
    ]
    assert sum(x["false_support"] for x in report["cases"]) == report["counts"]["false_supports"]
    assert all(isinstance(x["missed_conflicts"], list) for x in report["cases"])


def test_gold_labels_never_enter_product_input(monkeypatch):
    actual = bench.build_reality_state_from_evidence
    observed = []

    def recording(task, documents, **kwargs):
        observed.append((task, documents, kwargs))
        assert "gold" not in kwargs
        assert all("gold" not in doc for doc in documents)
        assert all("world_reference_claim" not in doc for doc in documents)
        return actual(task, documents, **kwargs)

    monkeypatch.setattr(bench, "build_reality_state_from_evidence", recording)
    bench.run_baseline(include_cases=False)
    assert len(observed) == 48


def test_reference_label_change_does_not_change_engine_predictions(tmp_path):
    original = bench.run_baseline()

    def change_gold(d):
        # A human re-annotation changes scoring, not production inputs.
        d["cases"][0]["gold"]["should_abstain"] = True

    changed = bench.run_baseline(_altered_fixture(tmp_path, change_gold))
    original_states = [(r["id"], r["predicted_status"]) for r in original["cases"]]
    changed_states = [(r["id"], r["predicted_status"]) for r in changed["cases"]]
    assert changed_states == original_states
    assert changed["counts"]["should_abstain"] == original["counts"]["should_abstain"] + 1
    assert changed["counts"]["safe_to_support"] == original["counts"]["safe_to_support"] - 1


def test_reference_claim_change_reduces_scoring_without_changing_predictions(tmp_path):
    original = bench.run_baseline()

    def corrupt_gold(d):
        d["cases"][0]["gold"]["expected_claims"][0]["text"] = (
            "An independently annotated claim missing from all evidence."
        )

    changed = bench.run_baseline(_altered_fixture(tmp_path, corrupt_gold))
    assert changed["counts"]["matched_claims"] == original["counts"]["matched_claims"] - 1
    assert changed["cases"][0]["predicted_status"] == original["cases"][0]["predicted_status"]


@pytest.mark.parametrize(
    "transform,reason",
    [
        (lambda d: d["cases"].append(d["cases"][0]), "unique case id"),
        (lambda d: d["cases"][0]["gold"].pop("should_abstain"), "independent abstention label"),
        (lambda d: d["cases"][0]["gold"].update(world_reference_is_simulated=False), "oracle must declare simulation"),
        (lambda d: d["cases"][0].update(scenario="unrecognized"), "unknown scenario"),
        (lambda d: d["cases"][0]["documents"][0].update(uri="https://real.example.com/fake"), "clearly fictional"),
        (lambda d: d["cases"][0]["gold"]["expected_claims"][0].update(source_refs=["https://not-in-input.test/"]), "invalid claim/source"),
        (lambda d: d["cases"][0]["gold"].update(expected_conflict_pairs=[["Unknown.", "Another."]]), "conflict refs unknown"),
    ],
)
def test_invalid_dataset_fails_loudly_instead_of_producing_scores(tmp_path, transform, reason):
    path = _altered_fixture(tmp_path, transform)
    with pytest.raises(ValueError, match=reason):
        bench.load_dataset(path)


def test_cli_can_write_deterministic_summary(tmp_path, capsys):
    destination = tmp_path / "report.json"
    assert bench.main(["--summary-only", "--output", str(destination)]) == 0
    saved = json.loads(destination.read_text(encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    assert saved == printed
    assert saved["case_count"] == 48
    assert "cases" not in saved


def test_dataset_can_be_replayed_without_network(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("benchmark unexpectedly attempted network access")

    monkeypatch.setattr("urllib.request.urlopen", no_network)
    assert bench.run_baseline(include_cases=False)["case_count"] == 48


def test_existing_fastapi_route_handler_preserves_submitted_evidence_contract():
    # HTTP transport itself is out of scope: this repository does not pin
    # Starlette's optional HTTP test-client dependency.
    case = bench.load_dataset()["cases"][0]
    request = EvidenceRealityStateRequest.model_validate({
        "task": case["task"],
        "entity": case["entity"],
        "documents": case["documents"],
        # No freshness policy: retain conservative uncertainty.
    })
    state = reality_state_from_evidence(request)
    assert state["status"] == "uncertain"
    assert state["claims"]["status"] == "usable"
    assert state["entity"]["name"] == case["entity"]


def test_computing_f1_handles_zero_and_undefined_counts():
    assert bench._f1(None, 1.0) is None
    assert bench._f1(0.0, 0.0) == 0.0
    assert bench._f1(0.5, 1.0) == pytest.approx(2 / 3)
    assert bench._ratio(0, 0) is None
