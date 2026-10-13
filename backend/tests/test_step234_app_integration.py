"""Step 234 offline probe-to-real-FastAPI contract test.

This uses the real API, middleware, model validation, orchestration and claim
alignment. Only the upstream publisher reader and HTTPS transport are replaced.
It is not independent externally deployed HTTPS evidence.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json

from fastapi.testclient import TestClient

from backend.app.evaluation.step234_external_https_pilot import (
    CLAIM, MAX_BODY_BYTES, SOURCE_EXCERPT, SOURCE_URL, TOKEN_ENV, run_probe,
)
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

PILOT_TOKEN = "step234-local-integration-only-not-a-real-secret"


def test_probe_runs_seven_checks_against_real_authenticated_api(monkeypatch):
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("ARL_PILOT_BEARER_TOKEN", PILOT_TOKEN)
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([SOURCE_URL]))
    monkeypatch.delenv(TOKEN_ENV, raising=False)
    observed_uris = []

    def fixed_publisher_observation(self, uri):
        # Exactly one reviewed publisher; reject any other URI. No network.
        observed_uris.append(uri)
        if uri != SOURCE_URL:
            raise ValueError("not an operator-allowlisted source URL")
        return {
            "uri": SOURCE_URL,
            "content": SOURCE_EXCERPT,
            "observed_quote_unit_sha256": [],
            "capture_sha256": sha256(SOURCE_EXCERPT.encode("utf-8")).hexdigest(),
            "capture_observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", fixed_publisher_observation)
    with TestClient(app) as client:
        def actual_api_transport(method, path, *, token=None, body=None, oversized=False):
            headers = {"Accept": "application/json"}
            if token is not None:
                headers["Authorization"] = "Bearer " + token
            if oversized:
                # Real middleware rejects this 4MiB+1 declared byte size
                # before request body parsing; no large upload in CI.
                headers["Content-Type"] = "application/json"
                headers["Content-Length"] = str(MAX_BODY_BYTES + 1)
                response = client.post(path, headers=headers, content=b"")
            elif method == "GET":
                response = client.get(path, headers=headers)
            else:
                response = client.post(path, headers=headers, json=body)
            return response.status_code, response.json()

        audit = run_probe(actual_api_transport, PILOT_TOKEN)

    assert audit["checks_passed"] == 7
    assert audit["complete_release_gate"] is False
    assert audit["independent_human_labeled_accuracy"] is False
    # No unauthenticated source fetching; two claim probes, plus the rejected
    # off-allowlist probe, reach backend independent-observation machinery.
    assert observed_uris == [SOURCE_URL, SOURCE_URL, "https://www.python.org/not-an-allowlisted-step234-path"]
    assert CLAIM not in json.dumps(audit)
    assert PILOT_TOKEN not in json.dumps(audit)
