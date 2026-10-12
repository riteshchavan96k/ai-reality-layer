"""Step 231 single-tenant pilot access tests (fake network only).

Genuine publisher TLS and deployed HTTP are tested separately in CI.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.api.pilot_auth import main, pilot_runtime_configuration
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader


URL = "https://www.python.org/downloads/release/python-3130/"
SECRET = "test-only-token-with-more-than-32-bytes-and-no-spaces"
CLAIM = "Python 3.13.0 is a stable release."


@pytest.fixture
def pilot(monkeypatch):
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("ARL_PILOT_BEARER_TOKEN", SECRET)
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([URL]))
    return TestClient(app)


def bearer(token=SECRET):
    return {"Authorization": "Bearer " + token}


def evidence_payload():
    return {
        "task": "Is Python 3.13.0 a stable release?",
        "entity": "Python 3.13.0",
        "documents": [{"uri": URL, "content": CLAIM}],
        "freshness_max_age_seconds": 3600,
        "require_independent_source_text_match": True,
        "require_claim_alignment": True,
        "claim_text": CLAIM,
    }


def test_missing_token_blocks_all_sensitive_routes_before_validation_or_fetch(pilot, monkeypatch):
    calls = []
    monkeypatch.setattr(
        AllowlistedHttpsSourceReader, "__call__",
        lambda self, uri: calls.append(uri),
    )
    for url in (
        "/api/v1/solve",
        "/api/v1/reality-state",
        "/api/v1/reality-state/evidence",
        "/openapi.json",
        "/docs",
        "/missing",
    ):
        response = pilot.post(url, json={"not": "even a valid request"})
        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["www-authenticate"] == "Bearer"
        assert "x-request-id" in response.headers
    assert calls == []


@pytest.mark.parametrize("header", [
    "",
    "Basic " + SECRET,
    "Bearer wrong-secret",
    "Bearer " + SECRET + " ",
    "Bearer " + SECRET + "\t",
    "Bearer " + ("A" * 600),
])
def test_wrong_or_malformed_authorization_never_reaches_pipeline(pilot, header):
    headers = {"Authorization": header} if header else {}
    response = pilot.post("/api/v1/reality-state/evidence", headers=headers, json=evidence_payload())
    assert response.status_code == 401
    assert SECRET not in response.text


def test_duplicate_authorization_header_rejected(pilot):
    response = pilot.post(
        "/api/v1/reality-state/evidence",
        headers=[("Authorization", "Bearer " + SECRET), ("Authorization", "Bearer " + SECRET)],
        json=evidence_payload(),
    )
    assert response.status_code == 401


def test_authenticated_pilot_executes_existing_strict_real_state_pipeline(pilot, monkeypatch):
    captured = []
    def fake_observation(self, uri):
        captured.append(uri)
        return {
            "uri": URL,
            "content": CLAIM,
            "observed_quote_unit_sha256": [],
            "capture_sha256": sha256(CLAIM.encode()).hexdigest(),
            "capture_observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", fake_observation)
    response = pilot.post(
        "/api/v1/reality-state/evidence",
        headers={**bearer(), "X-Request-ID": "pilot-test-231"},
        json=evidence_payload(),
    )
    assert response.status_code == 200, response.text
    assert response.headers["x-request-id"] == "pilot-test-231"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    result = response.json()
    assert result["status"] == "supported"
    assert result["evidence"]["claim_alignment"]["status"] == "aligned"
    assert captured == [URL]


def test_authorized_invalid_request_reaches_validation_not_business_logic(pilot):
    response = pilot.post("/api/v1/reality-state/evidence", headers=bearer(), json={})
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert "authorization" not in response.text.lower()
    assert SECRET not in response.text


def test_health_alone_remains_public_in_pilot(pilot):
    response = pilot.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "ai-reality-layer"
    assert pilot.get("/openapi.json").status_code == 401


@pytest.mark.parametrize("settings", [
    {"ARL_RUNTIME_MODE": "production"},
    {"ARL_RUNTIME_MODE": "pilot"},
    {"ARL_RUNTIME_MODE": "development", "ARL_PILOT_BEARER_TOKEN": SECRET},
    {"ARL_RUNTIME_MODE": "pilot", "ARL_PILOT_BEARER_TOKEN": "short"},
    {"ARL_RUNTIME_MODE": "pilot", "ARL_PILOT_BEARER_TOKEN": "x" * 300},
    {"ARL_RUNTIME_MODE": "pilot", "ARL_PILOT_BEARER_TOKEN": "a" * 32 + " "},
    {"ARL_RUNTIME_MODE": "pilot", "ARL_PILOT_BEARER_TOKEN": SECRET},
    {"ARL_RUNTIME_MODE": "pilot", "ARL_PILOT_BEARER_TOKEN": SECRET,
     "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": '["http://localhost/"]'},
    {"ARL_RUNTIME_MODE": "pilot", "ARL_PILOT_BEARER_TOKEN": SECRET,
     "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": "not json"},
])
def test_invalid_configuration_fails_closed(settings):
    with pytest.raises(ValueError):
        pilot_runtime_configuration(settings)


def test_invalid_pilot_config_refuses_requests_and_container_preflight(monkeypatch, capsys):
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.delenv("ARL_PILOT_BEARER_TOKEN", raising=False)
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([URL]))
    client = TestClient(app)
    r = client.post("/api/v1/reality-state", json={"task": "any"})
    assert r.status_code == 503
    assert r.json() == {"detail": "Service unavailable"}
    assert "x-request-id" in r.headers
    assert main() == 1
    assert "token" not in capsys.readouterr().out.lower()


def test_default_development_contract_unchanged(monkeypatch):
    monkeypatch.delenv("ARL_RUNTIME_MODE", raising=False)
    monkeypatch.delenv("ARL_PILOT_BEARER_TOKEN", raising=False)
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.post("/api/v1/reality-state/evidence", json={}).status_code == 422


def test_valid_config_preflight(pilot, capsys):
    assert main() == 0
    assert "valid" in capsys.readouterr().out


def test_oversized_authenticated_request_refused_before_evidence_processing(pilot, monkeypatch):
    calls = []
    monkeypatch.setattr(
        AllowlistedHttpsSourceReader, "__call__",
        lambda self, uri: calls.append(uri),
    )
    # This is an actual body byte check; do not rely on Content-Length alone.
    payload = b"x" * (4 * 1024 * 1024 + 1)
    response = pilot.post(
        "/api/v1/reality-state/evidence",
        headers={**bearer(), "Content-Type": "application/json"},
        content=payload,
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "Request body too large"}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers.get("x-request-id")
    assert calls == []


def test_oversized_unauthenticated_request_never_reaches_body_parser(pilot):
    response = pilot.post(
        "/api/v1/reality-state/evidence",
        content=b"x" * (4 * 1024 * 1024 + 1),
    )
    # Auth takes precedence: no token means no body validation/processing.
    assert response.status_code == 401


def test_pilot_rejects_json_object_allowlist_disguised_as_url_keys():
    with pytest.raises(ValueError):
        pilot_runtime_configuration({
            "ARL_RUNTIME_MODE": "pilot",
            "ARL_PILOT_BEARER_TOKEN": SECRET,
            "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS": json.dumps({URL: "not-a-list"}),
        })
