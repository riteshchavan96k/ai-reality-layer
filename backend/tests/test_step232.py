"""Offline Step 232 harness integrity tests. Live publisher data is tested in CI."""
from copy import deepcopy

import pytest

from backend.app.evaluation.step232_source_claim_safety import (
    DATASET_ID,
    SOURCES,
    Step232GateError,
    judge_case,
    load_dataset,
    main,
    summarize,
)


def _realistic_response(case, *, state=None, alignment=None, audit_ok=True):
    decision = alignment or case["expected_alignment"]
    status = state or ("supported" if case["expected_decision"] == "supported" else "uncertain")
    row = {"source_ref": SOURCES[case["source_id"]]}
    if audit_ok:
        row.update({
            "status": "exact_text_observed",
            "assertion_context_status": "unique_standalone_unit",
            "source_quote_context_status": "no_matching_html_quote_unit",
            "capture_sha256": "a" * 64,
            "capture_observed_at": "2026-10-13T00:00:00Z",
        })
    return {
        "status": status,
        "evidence": {
            "claim_alignment": {
                "status": decision,
                "source_count": 1,
                "source_decisions": [{"source_ref": SOURCES[case["source_id"]], "relationship": decision}],
                "decision_reasons": [{"source_ref": SOURCES[case["source_id"]], "code": {
                    "aligned": "bounded_assertion_aligned",
                    "contradicted": "bounded_assertion_contradicted",
                    "insufficient": "source_grammar_unsupported",
                }[decision]}],
                "factual_truth_verified": False,
                "semantic_support_verified": False,
            },
            "independent_source_text_assurance": {
                "publisher_authenticated": False,
                "semantic_support_verified": False,
                "sources": [row],
            },
        },
    }


def test_manifest_has_stable_predeclared_labels():
    dataset = load_dataset()
    assert dataset["dataset_id"] == DATASET_ID
    assert dataset["representative_population"] is False
    assert len(dataset["sources"]) == 2
    assert len(dataset["cases"]) == 12
    assert sum(x["reference_relation"] == "supports_claim" for x in dataset["cases"]) == 2


@pytest.mark.parametrize("mutator", [
    lambda d: d.update({"label_provenance": "independent_human_review"}),
    lambda d: d.update({"representative_population": True}),
    lambda d: d["sources"][0].update({"url": "http://localhost/secrets"}),
    lambda d: d["cases"].pop(),
    lambda d: d["cases"][0].update({"id": d["cases"][1]["id"]}),
    lambda d: d["cases"][0].update({"expected_decision": "abstain"}),
    lambda d: d["cases"][2].update({"expected_decision": "supported"}),
    lambda d: d["cases"][0].update({"excerpt": "x" * 501}),
])
def test_manifest_rejects_mutated_baseline(tmp_path, mutator):
    import json
    d = deepcopy(load_dataset())
    mutator(d)
    p = tmp_path / "tampered.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    with pytest.raises(Step232GateError):
        load_dataset(p)


def test_decision_checks_on_policy_without_claiming_population_accuracy():
    d = load_dataset()
    observations = [judge_case(case, _realistic_response(case)) for case in d["cases"]]
    result = summarize(d["cases"], observations)
    assert result["reference_positive_count"] == 2
    assert result["reference_positive_supported"] == 1
    assert result["reference_positive_abstained"] == 1
    assert result["reference_nonpositive_count"] == 10
    assert result["reference_nonpositive_falsely_supported"] == 0
    assert result["policy_conformant_count"] == 12
    assert result["population_factual_accuracy_established"] is False
    assert result["external_deployment_verified"] is False
    assert all("excerpt" not in item and "claim" not in item and "content" not in item
               for item in result["cases"])


def test_false_support_fails_closed_even_when_claim_alignment_insufficient():
    case = load_dataset()["cases"][3]
    with pytest.raises(Step232GateError):
        judge_case(case, _realistic_response(case, state="supported"))


def test_wrong_source_provenance_must_fail_even_for_correct_status():
    case = load_dataset()["cases"][0]
    response = _realistic_response(case)
    response["evidence"]["independent_source_text_assurance"]["sources"][0]["source_ref"] = SOURCES["ianareserved"]
    with pytest.raises(Step232GateError):
        judge_case(case, response)


@pytest.mark.parametrize("field", ["capture_sha256", "capture_observed_at"])
def test_supported_claim_requires_server_capture_metadata(field):
    case = load_dataset()["cases"][0]
    response = _realistic_response(case)
    response["evidence"]["independent_source_text_assurance"]["sources"][0].pop(field)
    with pytest.raises(Step232GateError):
        judge_case(case, response)


def test_claimed_independent_truth_or_publisher_authentication_must_fail():
    case = load_dataset()["cases"][0]
    for section, key in (
        ("claim_alignment", "factual_truth_verified"),
        ("claim_alignment", "semantic_support_verified"),
        ("independent_source_text_assurance", "publisher_authenticated"),
    ):
        response = _realistic_response(case)
        response["evidence"][section][key] = True
        with pytest.raises(Step232GateError):
            judge_case(case, response)


def test_network_not_enabled_implicitly():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_manifest_rejects_non_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"not": "complete"', encoding="utf-8")
    with pytest.raises(ValueError):
        load_dataset(path)
