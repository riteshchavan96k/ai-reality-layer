"""Step 227: bounded atomic assertion alignment, not semantic fact truth.

Fake source readers in tests are not real HTTPS publisher captures.
Existing Steps 222/226 hosted canaries independently test real network.
"""

from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.api.reality_state import RealityStateResponse
from backend.app.main import app
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.claim_assertion_alignment import (
    MAX_ATOMIC_CLAIM_CHARS, _parse_atomic, evaluate_claim_alignment,
)
from backend.app.reality.independent_source_text_assurance import IndependentSourceTextAssurance
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle


URL = "https://www.python.org/downloads/release/python-3130/"
URL2 = "https://www.iana.org/domains/reserved"
TRUE = "Python 3.13.0 was released on October 7, 2024."
FALSE = "Python 3.13.0 was released on January 1, 1900."
NEGATED = "Python 3.13.0 was not released on October 7, 2024."
UTC_NOW = datetime.now(timezone.utc)


def reader_for(mapping):
    def read(uri):
        content = mapping[uri]
        return {
            "uri": uri,
            "content": content,
            "capture_sha256": sha256(content.encode()).hexdigest(),
            "capture_observed_at": UTC_NOW.isoformat().replace("+00:00", "Z"),
        }
    return read


def make_state(claim=TRUE, content=TRUE, observed=None, *,
               documents=None, alignment=True, strict=True):
    observed = content if observed is None else observed
    reader = reader_for({URL: observed, URL2: observed})
    deps = replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(reader),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: UTC_NOW),
    )
    return build_reality_state_from_evidence(
        "Check the specific factual release-date assertion",
        documents or [{"uri": URL, "content": content}],
        dependencies=deps,
        freshness_max_age_seconds=3600,
        entity="Python 3.13.0",
        require_independent_source_text_match=strict,
        require_claim_alignment=alignment,
        claim_text=claim if alignment else None,
    )


def test_genuine_one_source_finite_grammar_alignment_preserves_structural_status():
    state = make_state()
    assert state["status"] == "supported"
    row = state["evidence"]["claim_alignment"]
    assert row["status"] == "aligned"
    assert row["source_count"] == 1
    assert row["source_decisions"][0] == {"source_ref": URL, "relationship": "aligned"}
    assert row["semantic_support_verified"] is False
    assert row["factual_truth_verified"] is False
    assert "explicit_atomic_claim_text_aligned_only" in state["confidence_signals"]["signals"]
    RealityStateResponse.model_validate(state)


@pytest.mark.parametrize("claim,quote,expected", [
    (TRUE, TRUE, "aligned"),
    (TRUE, FALSE, "contradicted"),
    (TRUE, NEGATED, "contradicted"),
    (NEGATED, TRUE, "contradicted"),
    (NEGATED, NEGATED, "aligned"),
    ("Python 3.13.0 is a stable release.", "Python 3.13.0 is a stable release.", "aligned"),
    ("Python 3.13.0 is a stable release.", "Python 3.13.0 is not a stable release.", "contradicted"),
    ("Python 3.13.0 is a stable release.", "Python 3.13.0 is a widely used programming language.", "insufficient"),
    (TRUE, "Python 3.12.0 was released on October 7, 2024.", "insufficient"),
    (TRUE, "Python 3.13.0 was released.", "insufficient"),
    (TRUE, "The claim that Python 3.13.0 was released on October 7, 2024 is false.", "insufficient"),
    (TRUE, '"Python 3.13.0 was released on October 7, 2024."', "insufficient"),
    (TRUE, "Python 3.13.0 was released on October 7, 2024. But this is disputed.", "insufficient"),
    (TRUE, "According to rumors Python 3.13.0 was released on October 7, 2024.", "insufficient"),
    (TRUE, "Python 3.13.0 was released on October 7, 2024. Python 3.13.0 is stable.", "insufficient"),
    (TRUE, "Python 3.13.0 was released on October 7, 2024.\nAnother text.", "insufficient"),
])
def test_independently_observed_atomic_quote_cases(claim, quote, expected):
    s = make_state(claim, quote)
    assert s["evidence"]["independent_source_text_assurance"]["status"] == "exact_text_observed"
    assert s["evidence"]["claim_alignment"]["status"] == expected
    assert s["status"] == ("supported" if expected == "aligned" else "uncertain")


def test_forged_claim_never_inherits_observer_capture():
    s = make_state(TRUE, FALSE, observed=TRUE)
    assert s["status"] == "uncertain"
    assert s["evidence"]["independent_source_text_assurance"]["status"] == "unverified"
    assert s["evidence"]["claim_alignment"]["status"] == "insufficient"


def test_mixed_source_conflict_refuses_support():
    docs = [{"uri": URL, "content": TRUE}, {"uri": URL2, "content": FALSE}]
    mapping = {URL: TRUE, URL2: FALSE}
    deps = replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(reader_for(mapping)),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: UTC_NOW),
    )
    result = build_reality_state_from_evidence(
        "What was the date?", docs, entity="Python 3.13.0",
        freshness_max_age_seconds=3600,
        require_independent_source_text_match=True,
        require_claim_alignment=True,
        claim_text=TRUE, dependencies=deps,
    )
    assert result["status"] == "uncertain"
    assert result["evidence"]["claim_alignment"]["status"] == "conflicting"
    assert [x["relationship"] for x in result["evidence"]["claim_alignment"]["source_decisions"]] == ["aligned", "contradicted"]


def test_no_capture_metadata_cannot_establish_claim_alignment():
    bundle = SubmittedEvidenceBundle.from_mappings([{"uri": URL, "content": TRUE}])
    strict = IndependentSourceTextAssurance(
        lambda uri: {"uri": uri, "content": TRUE}
    ).check(bundle)
    assert strict["status"] == "exact_text_observed"
    assert evaluate_claim_alignment(TRUE, bundle, strict)["status"] == "insufficient"


@pytest.mark.parametrize("payload", [
    {"require_claim_alignment": True},
    {"require_claim_alignment": True, "claim_text": TRUE},
    {"claim_text": TRUE},
    {"require_claim_alignment": "true", "require_independent_source_text_match": True, "claim_text": TRUE},
    {"require_claim_alignment": True, "require_independent_source_text_match": True, "claim_text": " "},
    {"require_claim_alignment": True, "require_independent_source_text_match": True, "claim_text": "X" * 501},
])
def test_bad_api_enrolment_is_rejected(payload):
    request = {"task": "Check claim", "documents": [{"uri": URL, "content": TRUE}]}
    request.update(payload)
    with pytest.raises(ValidationError):
        EvidenceRealityStateRequest.model_validate(request)


def test_no_opt_in_preserves_original_strict_behavior():
    s = make_state(FALSE, FALSE, alignment=False)
    assert s["status"] == "supported"
    assert "claim_alignment" not in s["evidence"]


def test_direct_python_caller_cannot_bypass_prerequisites():
    for kwargs in (
        {"require_claim_alignment": True, "claim_text": TRUE},
        {"require_claim_alignment": "yes", "require_independent_source_text_match": True, "claim_text": TRUE},
        {"claim_text": TRUE},
        {"require_claim_alignment": True, "require_independent_source_text_match": True},
    ):
        with pytest.raises(ValueError):
            build_reality_state_from_evidence("Check claim", [{"uri": URL, "content": TRUE}], **kwargs)


def test_actual_public_fastapi_route_with_fake_network_transport(monkeypatch):
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([URL]))
    from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
    monkeypatch.setattr(
        AllowlistedHttpsSourceReader, "__call__",
        lambda self, uri: reader_for({URL: FALSE})(uri),
    )
    response = TestClient(app).post("/api/v1/reality-state/evidence", json={
        "task": "Check the release claim",
        "documents": [{"uri": URL, "content": FALSE}],
        "entity": "Python 3.13.0",
        "freshness_max_age_seconds": 3600,
        "require_independent_source_text_match": True,
        "require_claim_alignment": True,
        "claim_text": TRUE,
    })
    assert response.status_code == 200
    assert response.json()["status"] == "uncertain"
    assert response.json()["evidence"]["claim_alignment"]["status"] == "contradicted"


def test_unknown_claim_and_bad_input_never_infer_semantics():
    assert _parse_atomic("The public release was exciting!") is None
    assert _parse_atomic("Python 3.13.0 might be stable.") is None
    assert _parse_atomic("x" * (MAX_ATOMIC_CLAIM_CHARS + 1)) is None
