"""Step249: real FastAPI pilot and fail-closed developer historical-timeline tests.

Original-source fetches here are intentionally mocked; a separate workflow
proves the API can read a timeline made using genuine Python.org HTTPS.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
import sqlite3
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.tests.test_step247 import (
    environment, SOURCE, OFFLIST, TOKEN, POSITIVE, NEGATIVE,
)
from backend.tests.test_step248 import baseline, append
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.api.temporal_timeline import TemporalTimelineRequest
from backend.app.cli import EXIT_BOUNDED
from backend.app.integrations.temporal_timeline_client import (
    TIMELINE_PATH, check_temporal_timeline_with_api,
    interpret_temporal_timeline,
)
from backend.app.main import app


def request(source=SOURCE, claim="Python 3.13.0 is a stable release."):
    return OriginalSourceClaimRequest(
        claim_text=claim, entity="Python 3.13.0",
        source_uri=source, freshness_max_age_seconds=3600.0,
    )


def body(root, *, claim=None):
    return TemporalTimelineRequest(
        root_record_id=root, claim=claim or request()
    ).model_dump(mode="json")


def build(environment, monkeypatch, *, linked=True):
    monkeypatch.setenv("ARL_TEMPORAL_HISTORY_API_ENABLED", "1")
    root = baseline()
    if linked:
        code, _ = append(root)
        assert code == EXIT_BOUNDED
        code, _ = append(root)
        assert code == EXIT_BOUNDED
    return root


def raw_api(root, token=TOKEN, *, req=None):
    with TestClient(app) as http:
        return http.post(
            TIMELINE_PATH, json=req or body(root),
            headers={"Authorization": "Bearer " + token},
        )


def assert_bounded(result, count):
    assert result.outcome == "verified_historical_timeline"
    assert result.reason_code == "operator_history_validated"
    assert len(result.observations) == count
    assert result.may_use_as_current_evidence is False
    assert result.factual_truth_verified is False
    assert result.publisher_authorship_verified is False
    assert result.historical_receipt_authenticated is False
    assert result.automatic_monitoring_enabled is False
    assert result.externally_deployed is False


def test_real_authenticated_local_fastapi_reads_three_entry_history_with_zero_egress(environment, monkeypatch):
    state, path = environment
    root = build(environment, monkeypatch)
    assert state["calls"] == 3
    before = path.read_bytes()
    with TestClient(app) as client:
        observed = check_temporal_timeline_with_api(client, TOKEN, request(), root)
        direct = client.post(
            TIMELINE_PATH, json=body(root),
            headers={"Authorization": "Bearer " + TOKEN},
        )
    assert_bounded(observed, 3)
    assert direct.status_code == 200
    assert direct.headers["cache-control"] == "no-store"
    assert direct.headers["x-content-type-options"] == "nosniff"
    assert direct.headers.get("x-request-id")
    raw = direct.json()
    assert raw["outcome"] == "verified_historical_timeline"
    assert raw["timeline"]["total_observations"] == 3
    assert raw["timeline"]["root_record_id"] == root
    assert raw["timeline"]["latest_record_id"] == observed.latest_record_id
    assert raw["timeline"]["historical_receipt_authenticated"] is False
    assert "source_uri" not in json.dumps(raw)
    assert POSITIVE not in json.dumps(raw)
    assert TOKEN not in json.dumps(raw)
    assert state["calls"] == 3
    assert path.read_bytes() == before


def test_valid_unlinked_baseline_is_readable_without_schema_writes(environment, monkeypatch):
    state, path = environment
    root = build(environment, monkeypatch, linked=False)
    before = path.read_bytes()
    with TestClient(app) as client:
        result = check_temporal_timeline_with_api(client, TOKEN, request(), root)
    assert_bounded(result, 1)
    assert result.observations[0].change_from_previous == "baseline"
    assert state["calls"] == 1
    assert path.read_bytes() == before
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='source_timeline_edges'"
        ).fetchone()[0] == 0


def test_history_disabled_by_default_even_with_valid_token(environment, monkeypatch):
    state, path = environment
    root = baseline()
    monkeypatch.delenv("ARL_TEMPORAL_HISTORY_API_ENABLED", raising=False)
    response = raw_api(root)
    assert response.status_code == 200
    assert response.json()["outcome"] == "abstain"
    assert response.json()["reason"] == "timeline_api_not_enabled"
    assert response.json()["timeline"] is None
    assert state["calls"] == 1


@pytest.mark.parametrize("token", ["", "invalid-token-with-nonmatching-value-"*2])
def test_wrong_or_missing_bearer_rejected(environment, monkeypatch, token):
    state, _ = environment
    root = build(environment, monkeypatch, linked=False)
    response = raw_api(root, token=token)
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    assert "no-store" == response.headers["cache-control"]
    assert state["calls"] == 1


def test_development_mode_cannot_read_history_even_with_api_optin(environment, monkeypatch):
    state, _ = environment
    root = baseline()
    monkeypatch.delenv("ARL_PILOT_BEARER_TOKEN")
    monkeypatch.setenv("ARL_RUNTIME_MODE", "development")
    monkeypatch.setenv("ARL_TEMPORAL_HISTORY_API_ENABLED", "1")
    response = raw_api(root)
    assert response.status_code == 200
    assert response.json()["outcome"] == "abstain"
    assert response.json()["timeline"] is None
    assert state["calls"] == 1


def test_offlist_source_request_cannot_read_history(environment, monkeypatch):
    state, _ = environment
    root = build(environment, monkeypatch, linked=False)
    response = raw_api(root, req=body(root, claim=request(source=OFFLIST)))
    assert response.status_code == 200
    assert response.json()["outcome"] == "abstain"
    assert response.json()["timeline"] is None
    assert state["calls"] == 1


def test_claim_mismatch_returns_no_partial_receipt(environment, monkeypatch):
    state, _ = environment
    root = build(environment, monkeypatch)
    response = raw_api(root, req=body(root, claim=request(claim=NEGATIVE)))
    assert response.status_code == 200
    assert response.json()["outcome"] == "abstain"
    assert response.json()["timeline"] is None
    assert POSITIVE not in response.text and state["calls"] == 3


@pytest.mark.parametrize("invalid", ["0"*32, "invalid", "A"*32, "../history"])
def test_unknown_or_invalid_root_never_exposes_partial_history(environment, monkeypatch, invalid):
    state, _ = environment
    root = build(environment, monkeypatch, linked=False)
    with TestClient(app) as client:
        result = client.post(TIMELINE_PATH, json={
            "claim": request().model_dump(mode="json"),
            "root_record_id": invalid,
        }, headers={"Authorization": "Bearer " + TOKEN})
    if len(invalid) != 32 or invalid != invalid.lower():
        assert result.status_code == 422
    else:
        assert result.status_code == 200
        assert result.json()["timeline"] is None
    assert state["calls"] == 1


def test_missing_db_never_created_by_history_api(environment, monkeypatch):
    state, path = environment
    monkeypatch.setenv("ARL_TEMPORAL_HISTORY_API_ENABLED", "1")
    assert not path.exists()
    response = raw_api("a"*32)
    assert response.status_code == 200
    assert response.json()["outcome"] == "abstain"
    assert not path.exists()
    assert state["calls"] == 0


def test_corrupt_timeline_fails_closed_without_source_reads(environment, monkeypatch):
    state, path = environment
    root = build(environment, monkeypatch)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE source_timeline_edges SET edge_mac=? WHERE sequence=2",
                   ("0"*64,))
    result = raw_api(root)
    assert result.status_code == 200
    assert result.json()["outcome"] == "abstain"
    assert result.json()["timeline"] is None
    assert state["calls"] == 3


def test_wrong_local_hmac_denies_history_api(environment, monkeypatch):
    state, _ = environment
    root = build(environment, monkeypatch, linked=False)
    monkeypatch.setenv("ARL_OBSERVATION_HMAC_KEY_HEX", "cc"*32)
    result = raw_api(root)
    assert result.json()["outcome"] == "abstain"
    assert result.json()["timeline"] is None
    assert state["calls"] == 1


def test_private_file_permissions_checked(environment, monkeypatch):
    state, path = environment
    root = build(environment, monkeypatch, linked=False)
    os.chmod(path, 0o644)
    result = raw_api(root)
    assert result.json()["outcome"] == "abstain"
    assert state["calls"] == 1


def test_server_rejects_extra_input_instead_of_ignoring(environment, monkeypatch):
    state, _ = environment
    root = build(environment, monkeypatch, linked=False)
    incoming = body(root)
    incoming["unexpected_field"] = "should-not-be-trusted"
    result = raw_api(root, req=incoming)
    assert result.status_code == 422
    assert state["calls"] == 1


@pytest.mark.parametrize("defect", [
    "false_is_integer", "fake_latest", "wrong_request", "extra_top_level",
    "extra_row", "duplicate_id", "backwards_time", "wrong_sequence",
    "false_change", "impossible_same_capture", "future_capture",
    "wrong_decision", "wrong_root", "missing_row",
    "wrong_count", "false_linkage", "wrong_history_flag",
    "stale_cannot_be_current",
])
def test_developer_client_rejects_untrusted_api_payload(environment, monkeypatch, defect):
    state, _ = environment
    root = build(environment, monkeypatch)
    real = raw_api(root).json()
    broken = deepcopy(real)
    timeline = broken["timeline"]
    observations = timeline["observations"]
    if defect == "false_is_integer":
        broken["factual_truth_verified"] = 0
    elif defect == "fake_latest":
        timeline["latest_record_id"] = root
    elif defect == "wrong_request":
        broken["request_binding_sha256"] = "0"*64
    elif defect == "extra_top_level":
        broken["trusted_publisher"] = True
    elif defect == "extra_row":
        observations[1]["injected"] = "irrelevant"
    elif defect == "duplicate_id":
        observations[2]["record_id"] = observations[1]["record_id"]
        timeline["latest_record_id"] = observations[1]["record_id"]
    elif defect == "backwards_time":
        observations[2]["source_capture_observed_at"] = "2020-01-01T00:00:00Z"
    elif defect == "wrong_sequence":
        observations[1]["sequence"] = 42
    elif defect == "false_change":
        observations[1]["change_from_previous"] = "bounded_statement_changed"
    elif defect == "impossible_same_capture":
        observations[1]["source_quote_sha256"] = "a"*64
        observations[1]["change_from_previous"] = "bounded_statement_changed"
    elif defect == "future_capture":
        observations[2]["source_capture_observed_at"] = "2999-01-01T00:00:00Z"
    elif defect == "wrong_decision":
        observations[1]["decision"] = "inferred_truth"
    elif defect == "wrong_root":
        broken["root_record_id"] = "f"*32
    elif defect == "missing_row":
        # Declared three-entry timeline cannot silently omit an observation.
        observations.pop()
    elif defect == "wrong_count":
        timeline["total_observations"] = 41
    elif defect == "false_linkage":
        timeline["linked_history"] = False
    elif defect == "wrong_history_flag":
        timeline["publisher_authorship_verified"] = True
    elif defect == "stale_cannot_be_current":
        broken["may_use_as_current_evidence"] = True
    answer = interpret_temporal_timeline(broken, request(), root)
    assert answer.outcome == "abstain"
    assert answer.observations == ()
    assert answer.latest_record_id is None
    assert state["calls"] == 3


@pytest.mark.parametrize("fault", ["network", "wrong_content_type", "huge_body", "server_error", "malformed_json"])
def test_developer_client_transport_failures_never_promote_history(environment, monkeypatch, fault):
    state, _ = environment
    root = build(environment, monkeypatch, linked=False)
    class FakeTransport:
        def post(self, path, *, json, headers):
            assert path == TIMELINE_PATH
            assert headers["Authorization"].startswith("Bearer ")
            if fault == "network":
                raise ConnectionError("private secret should never print")
            if fault == "server_error":
                return SimpleNamespace(
                    status_code=503, content=b"{}", headers={"content-type": "application/json"},
                    json=lambda: {},
                )
            if fault == "wrong_content_type":
                return SimpleNamespace(
                    status_code=200, content=b"{}", headers={"content-type": "text/html"},
                    json=lambda: {},
                )
            if fault == "huge_body":
                import backend.app.integrations.temporal_timeline_client as temporal
                return SimpleNamespace(
                    status_code=200, content=b"x"*(temporal.MAX_API_RESPONSE_BYTES + 1),
                    headers={"content-type": "application/json"}, json=lambda: {},
                )
            return SimpleNamespace(
                status_code=200, content=b"malformed",
                headers={"content-type": "application/json"},
                json=lambda: (_ for _ in ()).throw(ValueError("cannot parse")),
            )
    answer = check_temporal_timeline_with_api(FakeTransport(), TOKEN, request(), root)
    assert answer.outcome == "abstain"
    assert answer.observations == ()
    assert state["calls"] == 1


def test_invalid_client_root_and_short_token_inert(environment):
    state, _ = environment
    class NoIO:
        def post(self, *args, **kwargs):
            raise AssertionError("should not issue a request")
    outcome = check_temporal_timeline_with_api(NoIO(), "weak", request(), "a"*32)
    assert outcome.outcome == "abstain"
    outcome = check_temporal_timeline_with_api(NoIO(), TOKEN, request(), "../etc")
    assert outcome.outcome == "abstain"
    assert state["calls"] == 0


def test_old_historical_evidence_remains_historical_after_freshness_window(environment, monkeypatch):
    state, _ = environment
    root = build(environment, monkeypatch, linked=False)
    verified = raw_api(root).json()
    now = datetime.now(timezone.utc) + timedelta(days=30)
    result = interpret_temporal_timeline(verified, request(), root, now=now)
    assert_bounded(result, 1)
    assert result.may_use_as_current_evidence is False
    assert state["calls"] == 1
