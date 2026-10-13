"""End-to-end core claim-only API tests with a deterministic original-source reader.

Uses real FastAPI + strict orchestration. The upstream HTTPS observation is
a fake in this file: these cases prove contract behavior, NOT live publisher
origin, field factual accuracy or externally deployed service security.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader


URL = "https://www.python.org/downloads/release/python-3130/"
EXCERPT = "This is the stable release of Python 3.13.0"
TOKEN = "safe-test-only-token-no-network-very-long"


@pytest.fixture
def pilot(monkeypatch):
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("ARL_PILOT_BEARER_TOKEN", TOKEN)
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([URL]))
    return TestClient(app)


def payload(*, claim="Python 3.13.0 is a stable release.", uri=URL, entity="Python 3.13.0"):
    return {"claim_text": claim, "entity": entity, "source_uri": uri}


def post(pilot, request=None, *, token=TOKEN):
    return pilot.post(
        "/api/v1/reality-state/claim",
        json=payload() if request is None else request,
        headers={"Authorization": "Bearer " + token},
    )


def reader(monkeypatch, *, body=EXCERPT, quoted=False, stale=False, error=False):
    fetches = []

    def server_read(self, uri):
        fetches.append(uri)
        if error:
            raise RuntimeError("do not disclose publisher transport errors")
        stamp = datetime.now(timezone.utc) - (
            timedelta(days=365) if stale else timedelta(seconds=10)
        )
        return {
            "uri": uri,
            "content": body,
            "observed_quote_unit_sha256": (
                [sha256(EXCERPT.encode("utf-8")).hexdigest()] if quoted else []
            ),
            "capture_sha256": sha256(body.encode("utf-8")).hexdigest(),
            "capture_observed_at": stamp.isoformat().replace("+00:00", "Z"),
        }

    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", server_read)
    return fetches


def test_claim_only_endpoint_returns_bounded_supported_state_with_one_real_pipeline(pilot, monkeypatch):
    calls = reader(monkeypatch)
    response = post(pilot)
    assert response.status_code == 200, response.text
    value = response.json()
    assert value["status"] == "supported"
    assert value["reason"] == "bounded_reality_state_evaluated"
    assert value["source_ref"] == URL
    state = value["reality_state"]
    assert state["status"] == "supported"
    assert state["evidence"]["claim_alignment"]["status"] == "aligned"
    assert state["evidence"]["claim_alignment"]["decision_reasons"] == [
        {"source_ref": URL, "code": "bounded_assertion_aligned"}
    ]
    assert state["evidence"]["claim_alignment"]["semantic_support_verified"] is False
    assert state["evidence"]["claim_alignment"]["factual_truth_verified"] is False
    assert state["evidence"]["independent_source_text_assurance"]["sources"][0]["capture_sha256"]
    assert calls == [URL]  # One HTTPS source observation, no second fetch/drift
    assert response.headers["cache-control"] == "no-store"


def test_negative_assertion_does_not_get_supported(pilot, monkeypatch):
    calls = reader(monkeypatch)
    result = post(pilot, payload(claim="Python 3.13.0 is not a stable release."))
    assert result.status_code == 200
    state = result.json()
    assert state["status"] != "supported"
    assert state["reality_state"]["evidence"]["claim_alignment"]["status"] == "contradicted"
    assert calls == [URL]


@pytest.mark.parametrize("body", [
    "There is no evidence here.",
    EXCERPT + "\nPython 3.13.0 is not a stable release.",
    EXCERPT + "\n" + EXCERPT,
])
def test_missing_conflicting_or_repeated_relevant_units_abstain(pilot, monkeypatch, body):
    calls = reader(monkeypatch, body=body)
    result = post(pilot)
    assert result.status_code == 200
    value = result.json()
    assert value["status"] == "insufficient"
    assert value["reason"] == "no_unique_bounded_assertion"
    assert value["reality_state"] is None
    assert calls == [URL]


def test_quote_does_not_count_as_publisher_assertion(pilot, monkeypatch):
    calls = reader(monkeypatch, quoted=True)
    result = post(pilot)
    assert result.status_code == 200
    value = result.json()
    assert value["status"] != "supported"
    assert value["reality_state"]["evidence"]["claim_alignment"]["decision_reasons"] == [
        {"source_ref": URL, "code": "source_quoted_unit"}
    ]
    assert calls == [URL]


def test_stale_capture_cannot_become_supported(pilot, monkeypatch):
    reader(monkeypatch, stale=True)
    result = post(pilot)
    assert result.status_code == 200
    assert result.json()["status"] != "supported"


def test_unapproved_source_not_fetched(pilot, monkeypatch):
    calls = reader(monkeypatch)
    result = post(pilot, payload(uri="https://www.python.org/another-safe-looking-url"))
    assert result.status_code == 200
    assert result.json() == {
        "status": "unavailable",
        "reason": "source_not_operator_allowed",
        "source_ref": None,
        "reality_state": None,
    }
    assert calls == []


def test_unsupported_claim_grammar_refuses_fetch(pilot, monkeypatch):
    calls = reader(monkeypatch)
    result = post(pilot, payload(claim="Maybe Python 3.13.0 was stable?"))
    assert result.status_code == 200
    assert result.json()["reason"] == "claim_grammar_unsupported"
    assert calls == []


def test_reader_failure_is_sanitized(pilot, monkeypatch):
    calls = reader(monkeypatch, error=True)
    result = post(pilot)
    assert result.status_code == 200
    assert result.json()["status"] == "unavailable"
    assert result.json()["reason"] == "source_unavailable"
    assert "publisher transport errors" not in result.text
    assert calls == [URL]


def test_unconfigured_reader_fails_closed_in_development(monkeypatch):
    monkeypatch.delenv("ARL_RUNTIME_MODE", raising=False)
    monkeypatch.delenv("ARL_PILOT_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", raising=False)
    response = TestClient(app).post("/api/v1/reality-state/claim", json=payload())
    assert response.status_code == 200
    assert response.json()["reason"] == "reader_not_configured"
    assert response.json()["status"] == "unavailable"


def test_auth_gate_blocks_new_route_before_any_fetch(pilot, monkeypatch):
    calls = reader(monkeypatch)
    result = pilot.post("/api/v1/reality-state/claim", json=payload())
    assert result.status_code == 401
    assert result.json() == {"detail": "Unauthorized"}
    assert calls == []


@pytest.mark.parametrize("request", [
    {"claim_text": " ", "entity": "Python 3.13.0", "source_uri": URL},
    {"claim_text": "Python 3.13.0 is a stable release.", "entity": "", "source_uri": URL},
    {"claim_text": "Python 3.13.0 is a stable release.", "entity": "Python 3.13.0", "source_uri": "http://localhost/"},
    {**payload(), "unexpected_extracted_content": "forged"},
    {**payload(), "freshness_max_age_seconds": -1},
])
def test_strict_input_validation(pilot, request):
    result = post(pilot, request)
    assert result.status_code == 422


def test_source_payload_not_needed_from_ai_client(pilot, monkeypatch):
    calls = reader(monkeypatch)
    response = post(pilot, payload())
    assert response.status_code == 200
    assert calls == [URL]
    assert "documents" not in payload()
    assert "observed_at" not in payload()
