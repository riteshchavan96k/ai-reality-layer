"""Step 220: backend-only independent exact-text observer and strict support gate."""

from dataclasses import replace
import json
from pathlib import Path

from backend.app.evaluation import independent_source_assurance_benchmark as step220_benchmark
from datetime import datetime, timezone
from hashlib import sha256

import pytest
from pydantic import ValidationError

from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.api.reality_state import RealityStateResponse
from backend.app.main import reality_state_from_evidence
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.confidence_signal_aggregator import RealityConfidenceSignalAggregator
from backend.app.reality.independent_source_text_assurance import (
    MAX_INDEPENDENT_SOURCE_TEXT_CHARS,
    IndependentSourceTextAssurance,
)
from backend.app.reality.reality_state_builder import RealityStateBuilder
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle


NOW = datetime(2026, 1, 1, 13, tzinfo=timezone.utc)
URI = "https://publisher.example.test/releases"
TRUE_TEXT = "Python 3.13.0 was released on October 7, 2024."
FALSE_TEXT = "Python 3.13.0 was released on January 1, 1990."


def _doc(content=TRUE_TEXT, uri=URI):
    return {
        "uri": uri, "content": content,
        "observed_at": "2026-01-01T12:30:00Z",
    }


def _deps(reader=None):
    return replace(
        OrchestrationDependencies.default(),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
        reality_state_builder=RealityStateBuilder(clock=lambda: NOW),
        independent_source_text_assurance=IndependentSourceTextAssurance(reader),
    )


def _state(content=TRUE_TEXT, reader=None, strict=True, documents=None):
    return build_reality_state_from_evidence(
        "What is the release date of Python 3.13.0?",
        documents if documents is not None else [_doc(content)],
        entity="Python 3.13.0",
        freshness_max_age_seconds=3600,
        require_independent_source_text_match=strict,
        dependencies=_deps(reader),
    )


def _reader(expected=TRUE_TEXT, uri=URI):
    return lambda source_uri: {"uri": uri, "content": expected}


def _assurance(state):
    return state["evidence"]["independent_source_text_assurance"]


def test_unconfigured_strict_mode_fails_closed_not_silently_supported():
    state = _state()
    assert state["status"] == "uncertain"
    assert state["confidence_signals"]["claim_coverage"] == 1.0
    assert "independent_source_text_unverified" in state["confidence_signals"]["signals"]
    result = _assurance(state)
    assert result["status"] == "unverified"
    assert result["publisher_authenticated"] is False
    assert result["semantic_support_verified"] is False
    assert result["sources"][0]["reason"] == "independent_reader_unconfigured"
    assert result["sources"][0]["observer_content_sha256"] is None
    RealityStateResponse.model_validate(state)


def test_independent_exact_match_retains_on_topic_structural_support():
    separate_source_bytes = "Release history:\n" + TRUE_TEXT + "\nEarlier releases."
    state = _state(reader=_reader(expected=separate_source_bytes))
    assert state["status"] == "supported"
    assert "independent_source_exact_text_observed" in state["confidence_signals"]["signals"]
    assurance = _assurance(state)
    assert assurance["status"] == "exact_text_observed"
    assert assurance["matched_source_count"] == 1
    assert assurance["sources"][0]["observer_content_sha256"] == sha256(
        separate_source_bytes.encode("utf-8")
    ).hexdigest()
    assert assurance["publisher_authenticated"] is False


def test_official_url_with_forged_submitted_words_is_downgraded():
    state = _state(FALSE_TEXT, reader=_reader())
    assert state["status"] == "uncertain"
    assert state["confidence_signals"]["claim_coverage"] == 1.0
    assert "explicit_entity_text_alignment_only" in state["confidence_signals"]["signals"]
    assert "independent_source_text_unverified" in state["confidence_signals"]["signals"]
    assert _assurance(state)["sources"][0]["reason"] == "submitted_text_not_in_observed_content"


def test_wrong_topic_stays_uncertain_even_when_observer_matches_source_text():
    document = "Python 3.12.0 was released on October 2, 2023."
    state = _state(document, reader=_reader(expected=document))
    assert state["status"] == "uncertain"
    assert _assurance(state)["status"] == "exact_text_observed"
    assert "explicit_entity_not_aligned_with_all_linked_claims" in state["confidence_signals"]["signals"]


def test_two_sources_require_two_independent_matching_observations():
    second = "Python 3.13.0 is generally available."
    second_uri = URI + "/second"
    docs = [_doc(), _doc(second, uri=second_uri)]

    def provider(uri):
        return {"uri": uri, "content": TRUE_TEXT if uri == URI else "Unrelated source."}

    state = _state(reader=provider, documents=docs)
    assert state["status"] == "uncertain"
    assurance = _assurance(state)
    assert assurance["source_count"] == 2
    assert assurance["matched_source_count"] == 1
    assert assurance["sources"][1]["reason"] == "submitted_text_not_in_observed_content"


def test_two_sources_with_two_verified_observations_retain_support():
    second = "Python 3.13.0 is generally available."
    second_uri = URI + "/second"

    def provider(uri):
        return {"uri": uri, "content": TRUE_TEXT if uri == URI else second}

    state = _state(
        reader=provider, documents=[_doc(), _doc(second, uri=second_uri)]
    )
    assert state["status"] == "supported"
    assert _assurance(state)["matched_source_count"] == 2


@pytest.mark.parametrize("reader,reason", [
    (lambda _: None, "invalid_observer_response"),
    (lambda _: {"uri": URI + "/other", "content": TRUE_TEXT}, "observer_source_identity_mismatch"),
    (lambda _: {"uri": URI, "content": ""}, "invalid_observer_content"),
    (lambda _: {"uri": URI, "content": None}, "invalid_observer_content"),
    (lambda _: {"uri": URI, "content": TRUE_TEXT * 10000}, "observer_content_over_limit"),
    (lambda _: (_ for _ in ()).throw(RuntimeError("private auth secret")), "observer_unavailable"),
])
def test_bad_observer_results_fail_closed_without_leaking_exceptions(reader, reason):
    state = _state(reader=reader)
    assert state["status"] == "uncertain"
    assurance = _assurance(state)
    assert assurance["status"] == "unverified"
    assert assurance["sources"][0]["reason"] == reason
    assert "private auth secret" not in repr(assurance)


def test_source_capture_size_limit_is_strict():
    assert MAX_INDEPENDENT_SOURCE_TEXT_CHARS == 200_000
    result = IndependentSourceTextAssurance(
        _reader(expected="A" * 200_001)
    ).check(SubmittedEvidenceBundle.from_mappings([_doc()]))
    assert result["sources"][0]["reason"] == "observer_content_over_limit"


def test_hash_provided_by_caller_is_not_trusted_as_content_proof():
    doctored = _doc(FALSE_TEXT)
    doctored["source_content_verified"] = True
    doctored["observer_content_sha256"] = sha256(TRUE_TEXT.encode()).hexdigest()
    # Python interface ignores caller-controlled extra fields; API rejects them.
    state = _state(reader=_reader(), documents=[doctored])
    assert state["status"] == "uncertain"
    assert _assurance(state)["matched_source_count"] == 0
    with pytest.raises(ValidationError):
        EvidenceRealityStateRequest.model_validate({
            "task": "Check the date",
            "documents": [doctored],
            "require_independent_source_text_match": True,
        })


@pytest.mark.parametrize("value", ["true", 1, None, 0.0, []])
def test_api_opt_in_requires_literal_boolean(value):
    with pytest.raises(ValidationError):
        EvidenceRealityStateRequest.model_validate({
            "task": "Check the date",
            "documents": [_doc()],
            "require_independent_source_text_match": value,
        })


def test_default_legacy_path_does_not_claim_to_have_checked_source_content():
    state = _state(FALSE_TEXT, reader=None, strict=False)
    assert state["status"] == "supported"
    assert "independent_source_text_assurance" not in state["evidence"]
    assert not any(
        "independent_source_" in signal
        for signal in state["confidence_signals"]["signals"]
    )


def test_strict_request_calls_existing_fastapi_route_with_fail_closed_default():
    request = EvidenceRealityStateRequest.model_validate({
        "task": "What is the release date of Python 3.13.0?",
        "entity": "Python 3.13.0",
        "documents": [_doc()],
        "require_independent_source_text_match": True,
    })
    assert request.require_independent_source_text_match is True
    response = reality_state_from_evidence(request)
    assert response["status"] == "uncertain"
    assert response["evidence"]["independent_source_text_assurance"]["status"] == "unverified"


def test_direct_caller_cannot_turn_a_non_boolean_mode_on_or_off():
    with pytest.raises(ValueError, match="must be boolean"):
        build_reality_state_from_evidence(
            "Check date", [_doc()],
            require_independent_source_text_match="no",
        )


def test_empty_source_reader_is_not_a_configured_capture():
    assert IndependentSourceTextAssurance().check(
        SubmittedEvidenceBundle.from_mappings([_doc()])
    )["status"] == "unverified"


def test_strict_mode_retains_freshness_uncertainty_even_with_independent_text():
    result = build_reality_state_from_evidence(
        "Check Python 3.13.0", [_doc()],
        entity="Python 3.13.0",
        require_independent_source_text_match=True,
        dependencies=_deps(_reader()),
    )
    assert _assurance(result)["status"] == "exact_text_observed"
    assert result["status"] == "uncertain"
    assert "freshness_uncertain" in result["confidence_signals"]["signals"]


def test_source_text_match_is_not_semantic_support_or_world_truth():
    fake_but_observed = "Python 3.13.0 was released on January 1, 1990."
    result = _state(fake_but_observed, reader=_reader(expected=fake_but_observed))
    assert result["status"] == "supported"
    # A malicious/misconfigured reader that repeats a false document is NOT
    # an independent publisher authentication, despite exact matching.
    assert _assurance(result)["publisher_authenticated"] is False
    assert _assurance(result)["semantic_support_verified"] is False


def test_direct_aggregator_rejects_unrecognized_assurance_status():
    with pytest.raises(ValueError, match="status is invalid"):
        RealityConfidenceSignalAggregator().aggregate_result(
            {"status": "usable"},
            {"status": "usable", "claim_count": 1, "linked_claim_count": 1},
            {"status": "usable", "stale_count": 0, "unknown_count": 0},
            {"status": "empty", "conflict_count": 0},
            independent_source_text_status="source_authenticated",
        )


def test_committed_step220_scorecard_equals_replayed_current_strict_pipeline():
    path = Path(__file__).resolve().parents[2] / "docs" / "STEP_220_SCORECARD.json"
    saved = json.loads(path.read_text(encoding="utf-8"))
    replayed = step220_benchmark.run_baseline()
    assert saved == replayed


def test_step220_benchmark_records_legitimate_abstention_tradeoff_honestly():
    scored = step220_benchmark.run_baseline()
    assert scored["case_count"] == 48
    assert scored["counts"]["abstain_required"] == 40
    assert scored["counts"]["legitimate_cases"] == 8
    assert scored["counts"]["legitimate_supported"] == 8
    assert scored["metrics"]["false_support_rate"] == 0
    assert scored["metrics"]["legitimate_support_rate"] == 1
    # Without a trusted operator reader, the product correctly avoids
    # unsupported promotion, but cannot support even benign snippets.
    assert scored["metrics"]["unconfigured_legitimate_support_rate"] == 0
    assert "not-publisher-authenticated" in scored["corpus_type"]
    assert any("not actual publisher captures" in item for item in scored["limitations"])


def test_benchmark_does_not_depend_on_network_access(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("offline benchmark unexpectedly used the network")
    monkeypatch.setattr("urllib.request.urlopen", blocked)
    assert step220_benchmark.run_baseline()["case_count"] == 48
