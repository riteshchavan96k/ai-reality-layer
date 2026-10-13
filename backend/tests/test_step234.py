"""Offline Step 234 verifier contract tests: no DNS or external HTTPS in CI.

These fakes cannot establish a deployed system; live verification requires a
separately authorized operator hostname and external independent client.
"""
from hashlib import sha256
import socket

import pytest

from backend.app.evaluation.step234_external_https_pilot import (
    CLAIM, NEGATED_CLAIM, SOURCE_URL, ExternalPilotClient, PilotProbeError,
    _global_dns_records, main, run_probe, validate_endpoint,
)

TOKEN = "test-only-234-token-at-least-thirty-two-characters-long"


def fake_remote(*, wrong_receipt=False, positive_status="supported", bad_source_status="insufficient",
                positive_semantic=False, negation_status="uncertain"):
    calls = []

    def send(method, path, *, token=None, body=None, oversized=False):
        calls.append((method, path, token, body, oversized))
        if method == "GET":
            return 200, {"status": "healthy", "service": "ai-reality-layer"}
        if token not in (TOKEN,):
            return 401, {"detail": "Unauthorized"}
        if oversized:
            return 413, {"detail": "Request body too large"}
        if body["documents"][0]["uri"] != SOURCE_URL:
            return 200, {"status": bad_source_status}
        claim = body["claim_text"]
        if claim == CLAIM:
            return 200, {"status": positive_status, "evidence": {
                "claim_alignment": {
                    "status": "aligned", "semantic_support_verified": positive_semantic,
                    "factual_truth_verified": False,
                    "decision_reasons": [{"source_ref": SOURCE_URL, "code": "bounded_assertion_aligned"}],
                },
                "independent_source_text_assurance": {"sources": [{
                    "source_ref": SOURCE_URL,
                    "capture_sha256": "bad" if wrong_receipt else sha256(b"source").hexdigest(),
                    "capture_observed_at": "2026-10-13T08:00:00Z",
                }]},
            }}
        if claim == NEGATED_CLAIM:
            return 200, {"status": negation_status, "evidence": {
                "claim_alignment": {"status": "contradicted", "decision_reasons": [
                    {"source_ref": SOURCE_URL, "code": "bounded_assertion_contradicted"}]
                }
            }}
        raise AssertionError("unexpected fake case")

    return send, calls


def test_bounded_offline_probe_verifies_seven_distinct_public_http_behaviors():
    send, calls = fake_remote()
    result = run_probe(send, TOKEN)
    assert result["checks_passed"] == 7
    assert result["complete_release_gate"] is False
    assert result["independent_human_labeled_accuracy"] is False
    assert len(calls) == 7
    assert calls[0][0:2] == ("GET", "/health")
    assert calls[1][2] is None and calls[2][2] == TOKEN + "-incorrect"
    assert calls[3][4] is True and calls[3][3] is None
    assert calls[4][3]["claim_text"] == CLAIM
    assert calls[5][3]["claim_text"] == NEGATED_CLAIM
    assert calls[6][3]["documents"][0]["uri"] != SOURCE_URL
    assert TOKEN not in str(result)
    assert CLAIM not in str(result)


@pytest.mark.parametrize("broken", [
    {"wrong_receipt": True},
    {"positive_status": "uncertain"},
    {"positive_semantic": True},
    {"negation_status": "supported"},
    {"bad_source_status": "supported"},
])
def test_probe_fails_closed_on_false_success_or_missing_capture(broken):
    send, _ = fake_remote(**broken)
    with pytest.raises(PilotProbeError):
        run_probe(send, TOKEN)


@pytest.mark.parametrize("bad", [
    "http://pilot.example.org", "https://127.0.0.1", "https://[::1]",
    "https://localhost", "https://pilot.local", "https://pilot.internal",
    "https://pilot.example.org:8080", "https://pilot.example.org/path",
    "https://pilot.example.org/?token=leak", "https://pilot.example.org/#fragment",
    "https://user:password@pilot.example.org", "https://pilot.example.org@bad.local",
    "https://pilot.example.org.evil.test", "https://pilot..org", "https://pilot.org.",
    "https://pilot_unsafe.org", "https://éxample.org", "",
])
def test_endpoint_rejects_unsafe_or_non_external_origin(bad):
    with pytest.raises(PilotProbeError):
        validate_endpoint(bad)


def test_endpoint_accepts_only_standard_https_dns_origin():
    assert validate_endpoint("https://pilot.example.org") == "pilot.example.org"
    assert validate_endpoint("https://PILOT.EXAMPLE.ORG:443/") == "pilot.example.org"


def test_original_transport_does_not_support_unreviewed_paths_or_methods():
    client = ExternalPilotClient("https://pilot.example.org")
    with pytest.raises(PilotProbeError):
        client.send("POST", "/api/v1/solve", token=TOKEN)
    with pytest.raises(PilotProbeError):
        client.send("GET", "/openapi.json")
    with pytest.raises(PilotProbeError):
        client.send("POST", "/api/v1/reality-state/evidence", oversized=True, body={})


def test_dns_rejects_private_and_mixed_addresses(monkeypatch):
    def record(ip):
        return (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (ip, 443))
    for data in ([record("127.0.0.1")], [record("8.8.8.8"), record("10.1.2.3")]):
        monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: data)
        with pytest.raises(PilotProbeError, match="endpoint_dns_not_global"):
            _global_dns_records("pilot.example.org")
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [record("8.8.8.8")])
    assert _global_dns_records("pilot.example.org")


def test_fails_off_without_explicit_live_flag_or_secret(monkeypatch, capsys):
    monkeypatch.delenv("ARL_STEP234_PROBE_BEARER_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        main(["--endpoint", "https://pilot.example.org"])
    # --live with invalid origin cannot attempt any network.
    assert main(["--endpoint", "http://pilot.example.org", "--live"]) == 1
    assert "probe failed" in capsys.readouterr().out.lower()


def test_probe_does_not_echo_invalid_secret_in_error():
    send, _ = fake_remote()
    for token in ("short", "has spaces " + TOKEN, "♡" + TOKEN):
        with pytest.raises(PilotProbeError, match="probe_secret_invalid") as exc:
            run_probe(send, token)
        assert token not in str(exc.value)
