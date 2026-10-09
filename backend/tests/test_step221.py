"""Step 221: exact-URL HTTPS reader, public DNS pinning, source-capture audit.

Tests use backend-injected fake HTTPS transports and DNS/socket spies,
not live or authenticated publisher captures.
"""

from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json
import socket
import ssl
from unittest.mock import Mock

import pytest

from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.api.reality_state import RealityStateResponse
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality import allowlisted_https_source_reader as reader_module
from backend.app.reality.allowlisted_https_source_reader import (
    AllowlistedHttpsSourceReader, _checked_global_addresses,
    _decode_observed_content, _PinnedHttpsConnection,
)
from backend.app.reality.independent_source_text_assurance import (
    IndependentSourceTextAssurance,
)
from backend.app.reality.reality_state_builder import RealityStateBuilder
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator


URI = "https://publisher.example.test/releases/3.13?edition=full"
ENTITY = "Python 3.13.0"
CORRECT = "Python 3.13.0 was released on October 7, 2024."
FALSE = "Python 3.13.0 was released on January 1, 1990."
NOW = datetime(2026, 10, 9, 18, 30, tzinfo=timezone.utc)
OBSERVED = "2026-10-09T18:00:00Z"


class FakeResponse:
    def __init__(self, body: bytes, *, status=200, headers=None):
        self.status = status
        self.body = body
        self.headers = headers or {"Content-Type": "text/html; charset=utf-8"}

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

    def read(self, bound):
        return self.body[:bound]


class FakeConnection:
    instances = []
    response = FakeResponse(b"")
    error = None

    def __init__(self, host, port, *, timeout, context):
        self.host, self.port, self.timeout, self.context = (
            host, port, timeout, context
        )
        self.request_args = None
        self.closed = False
        type(self).instances.append(self)

    def request(self, method, path, *, headers):
        self.request_args = (method, path, headers)
        if type(self).error:
            raise type(self).error

    def getresponse(self):
        return type(self).response

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def reset_transport():
    FakeConnection.instances = []
    FakeConnection.error = None
    FakeConnection.response = FakeResponse(b"")


def _reader(body=None, *, status=200, headers=None):
    if body is None:
        body = (
            "<html><head><title>title</title></head><body>"
            "<p>Python 3.13.0 was released on <strong>October 7, 2024.</strong></p>"
            "<script>malicious scripted text</script></body></html>"
        ).encode()
    FakeConnection.response = FakeResponse(body, status=status, headers=headers)
    return AllowlistedHttpsSourceReader(
        [URI], clock=lambda: NOW, connection_factory=FakeConnection
    )


def _deps(source_reader):
    return replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(source_reader),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
        reality_state_builder=RealityStateBuilder(clock=lambda: NOW),
    )


def _state(reader, excerpt=CORRECT, uri=URI):
    return build_reality_state_from_evidence(
        "What is the release date of Python 3.13.0?",
        [{"uri": uri, "content": excerpt, "observed_at": OBSERVED}],
        freshness_max_age_seconds=3600, entity=ENTITY,
        require_independent_source_text_match=True,
        dependencies=_deps(reader),
    )


def _dns(address):
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    addr = (address, 443, 0, 0) if family == socket.AF_INET6 else (address, 443)
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", addr)


def test_real_reader_uses_exact_allowlisted_https_target_and_tls_checks():
    reader = _reader()
    result = reader(URI)
    assert result["uri"] == URI
    assert result["content"] == CORRECT
    assert "scripted" not in result["content"]
    assert result["capture_sha256"] == sha256(FakeConnection.response.body).hexdigest()
    assert result["capture_observed_at"] == "2026-10-09T18:30:00Z"
    assert len(FakeConnection.instances) == 1
    conn = FakeConnection.instances[0]
    assert conn.host == "publisher.example.test"
    assert conn.port == 443
    assert conn.timeout == 5.0
    assert isinstance(conn.context, ssl.SSLContext)
    assert conn.context.verify_mode == ssl.CERT_REQUIRED
    assert conn.context.check_hostname is True
    assert conn.request_args[0] == "GET"
    assert conn.request_args[1] == "/releases/3.13?edition=full"
    assert conn.request_args[2]["Accept-Encoding"] == "identity"
    assert conn.closed is True


def test_source_capture_metadata_reaches_existing_reality_state():
    source_reader = _reader()
    output = _state(source_reader)
    RealityStateResponse.model_validate(output)
    assert output["status"] == "supported"
    observer = output["evidence"]["independent_source_text_assurance"]
    assert observer["status"] == "exact_text_observed"
    assert observer["publisher_authenticated"] is False
    assert observer["semantic_support_verified"] is False
    assert observer["sources"][0]["capture_sha256"] == sha256(
        FakeConnection.response.body
    ).hexdigest()
    assert observer["sources"][0]["capture_observed_at"] == "2026-10-09T18:30:00Z"


def test_forged_excerpt_does_not_pass_real_reader_comparison():
    source_reader = _reader()
    state = _state(source_reader, excerpt=FALSE)
    assert state["status"] == "uncertain"
    assert state["evidence"]["independent_source_text_assurance"]["sources"][0][
        "reason"
    ] == "submitted_text_not_in_observed_content"


def test_wrong_topic_stays_uncertain_even_if_page_contains_it():
    source_reader = _reader(body=b"<p>Python 3.12.0 was released earlier.</p>")
    state = _state(source_reader, excerpt="Python 3.12.0 was released earlier.")
    assert state["status"] == "uncertain"
    assert "explicit_entity_not_aligned_with_all_linked_claims" in (
        state["confidence_signals"]["signals"]
    )


def test_unallowlisted_source_fails_closed_before_transport_creation():
    source_reader = _reader()
    with pytest.raises(ValueError, match="not operator allowlisted"):
        source_reader("https://publisher.example.test/private")
    assert FakeConnection.instances == []
    output = _state(source_reader, uri="https://publisher.example.test/private")
    assert output["status"] == "uncertain"
    assert FakeConnection.instances == []


@pytest.mark.parametrize("invalid", [
    [], ["http://example.com"], ["https://127.0.0.1/private"],
    ["https://localhost/home"], ["https://example.com:444/"],
    ["https://user:password@example.com/home"],
    ["https://example.com/#fragment"],
    ["https://example.com/a"] * 2,
    ["https://example.com/a"] * 21,
    "https://example.com/path",
])
def test_invalid_allowlist_fails_closed_at_constructor(invalid):
    with pytest.raises(ValueError):
        AllowlistedHttpsSourceReader(invalid)


@pytest.mark.parametrize("settings", [
    {"timeout_seconds": 0}, {"timeout_seconds": 16},
    {"timeout_seconds": float("nan")}, {"timeout_seconds": True},
    {"max_response_bytes": 0}, {"max_response_bytes": 1_000_001},
    {"max_response_bytes": True},
])
def test_reader_resource_settings_are_bounded(settings):
    with pytest.raises(ValueError):
        AllowlistedHttpsSourceReader([URI], **settings)


@pytest.mark.parametrize("address", [
    "127.0.0.1", "10.0.0.2", "172.16.0.1", "192.168.1.1",
    "169.254.169.254", "::1", "fe80::1", "fc00::1", "0.0.0.0",
])
def test_dns_private_and_link_local_ip_returns_are_rejected(monkeypatch, address):
    monkeypatch.setattr(
        reader_module.socket, "getaddrinfo",
        lambda *args, **kwargs: [_dns(address)],
    )
    with pytest.raises(ValueError, match="non-global"):
        _checked_global_addresses("publisher.example.test")


def test_mixed_global_and_local_dns_answer_is_rejected_not_fallen_back(monkeypatch):
    monkeypatch.setattr(
        reader_module.socket, "getaddrinfo",
        lambda *args, **kwargs: [_dns("8.8.8.8"), _dns("127.0.0.1")],
    )
    with pytest.raises(ValueError, match="non-global"):
        _checked_global_addresses("publisher.example.test")


def test_valid_public_address_resolves_once(monkeypatch):
    count = []
    def resolver(host, port, **kwargs):
        count.append((host, port))
        return [_dns("8.8.8.8")]
    monkeypatch.setattr(reader_module.socket, "getaddrinfo", resolver)
    assert _checked_global_addresses("publisher.example.test")[0][3] == ("8.8.8.8", 443)
    assert count == [("publisher.example.test", 443)]


def test_pinned_https_connection_uses_resolved_ip_and_original_hostname(monkeypatch):
    monkeypatch.setattr(
        reader_module, "_checked_global_addresses",
        lambda host: [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, ("8.8.8.8", 443))],
    )
    raw = Mock()
    monkeypatch.setattr(reader_module.socket, "socket", lambda *args: raw)
    ctx = Mock()
    ctx.wrap_socket.return_value = Mock()
    conn = _PinnedHttpsConnection(
        "publisher.example.test", 443, timeout=3, context=ctx
    )
    conn.connect()
    raw.settimeout.assert_called_once_with(3)
    raw.connect.assert_called_once_with(("8.8.8.8", 443))
    ctx.wrap_socket.assert_called_once_with(
        raw, server_hostname="publisher.example.test"
    )
    assert conn.sock == ctx.wrap_socket.return_value


def test_handshake_failure_closes_unverified_socket(monkeypatch):
    monkeypatch.setattr(
        reader_module, "_checked_global_addresses",
        lambda host: [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, ("8.8.8.8", 443))],
    )
    raw = Mock()
    monkeypatch.setattr(reader_module.socket, "socket", lambda *args: raw)
    ctx = Mock()
    ctx.wrap_socket.side_effect = ssl.SSLError("bad certificate")
    conn = _PinnedHttpsConnection("publisher.example.test", 443, timeout=3, context=ctx)
    with pytest.raises(ssl.SSLError):
        conn.connect()
    raw.close.assert_called_once()


@pytest.mark.parametrize("status,headers,body", [
    (302, {"Location": "https://localhost/admin", "Content-Type": "text/plain"}, b"redirect"),
    (404, {"Content-Type": "text/plain"}, b"absent"),
    (500, {"Content-Type": "text/plain"}, b"error"),
    (200, {"Content-Type": "application/json"}, b'{"ok": true}'),
    (200, {"Content-Type": "text/html", "Content-Encoding": "gzip"}, b"compressed"),
    (200, {"Content-Type": "text/plain", "Content-Length": "bogus"}, b"xx"),
    (200, {"Content-Type": "text/plain", "Content-Length": "999999"}, b"xx"),
    (200, {"Content-Type": "text/plain", "Content-Length": "999"}, b"short"),
    (200, {"Content-Type": "text/plain; charset=iso-8859-1"}, b"something"),
    (200, {"Content-Type": "text/plain"}, b"\xff"),
    (200, {"Content-Type": "text/html"}, b"<script>hidden</script>"),
])
def test_invalid_http_source_never_grants_assurance(status, headers, body):
    reader = _reader(body=body, status=status, headers=headers)
    result = _state(reader)
    assert result["status"] == "uncertain"
    assert result["evidence"]["independent_source_text_assurance"]["status"] == "unverified"
    assert FakeConnection.instances[0].closed is True


def test_above_size_response_rejected_without_reading_unbounded_body():
    reader = AllowlistedHttpsSourceReader(
        [URI], max_response_bytes=32,
        connection_factory=FakeConnection, clock=lambda: NOW
    )
    FakeConnection.response = FakeResponse(
        b"X" * 33, headers={"Content-Type": "text/plain"}
    )
    assert _state(reader)["status"] == "uncertain"


def test_html_parser_recombines_visible_text_without_hidden_script_or_head():
    text = _decode_observed_content(
        b"<html><head><title>secret</title></head><body>Alpha <b>Beta</b>"
        b"<script>deception</script><style>bad</style> &amp; gamma</body></html>",
        "text/html; charset=utf-8",
    )
    assert text == "Alpha Beta & gamma"


@pytest.mark.parametrize("metadata", [
    {"capture_sha256": "not-a-digest", "capture_observed_at": "2026-10-09T18:30:00Z"},
    {"capture_sha256": "a" * 64},
    {"capture_observed_at": "2026-10-09T18:30:00Z"},
    {"capture_sha256": "a" * 64, "capture_observed_at": "not-a-dateZ"},
])
def test_invalid_operator_capture_metadata_not_accepted(metadata):
    reader = lambda uri: {"uri": uri, "content": CORRECT, **metadata}
    state = _state(reader)
    assert state["status"] == "uncertain"
    assert state["evidence"]["independent_source_text_assurance"]["sources"][0][
        "reason"
    ] == "invalid_observer_capture_metadata"


def test_env_off_by_default_and_configured_only_from_server(monkeypatch):
    monkeypatch.delenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", raising=False)
    assert OrchestrationDependencies.default().independent_source_text_assurance._reader is None
    monkeypatch.setenv(
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([URI])
    )
    obs = OrchestrationDependencies.default().independent_source_text_assurance
    assert isinstance(obs._reader, AllowlistedHttpsSourceReader)
    with pytest.raises(ValueError, match="not operator allowlisted"):
        obs._reader("https://publisher.example.test/not-allowed")


@pytest.mark.parametrize("config", [
    "not json", "{}", '"https://example.com"', "[]",
    '["http://example.com"]', '["https://127.0.0.1"]',
])
def test_bad_operator_env_configuration_never_silently_enables_reader(monkeypatch, config):
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", config)
    with pytest.raises(ValueError):
        OrchestrationDependencies.default()


def test_no_network_in_default_unconfigured_reader(monkeypatch):
    monkeypatch.delenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", raising=False)
    def blocked(*args, **kwargs):
        raise AssertionError("unexpected network access")
    monkeypatch.setattr(reader_module.socket, "getaddrinfo", blocked)
    request = EvidenceRealityStateRequest.model_validate({
        "task": "Release date?",
        "entity": ENTITY,
        "documents": [{"uri": URI, "content": CORRECT, "observed_at": OBSERVED}],
        "require_independent_source_text_match": True,
        "freshness_max_age_seconds": 3600,
    })
    assert request.require_independent_source_text_match
    result = _state(OrchestrationDependencies.default().independent_source_text_assurance._reader)
    assert result["status"] == "uncertain"


def test_operator_capture_does_not_claim_factual_truth():
    # Even genuinely observed publisher text can be incorrect in the world.
    reader = _reader(body=FALSE.encode(), headers={"Content-Type": "text/plain"})
    state = _state(reader, excerpt=FALSE)
    assert state["status"] == "supported"
    assurance = state["evidence"]["independent_source_text_assurance"]
    assert assurance["publisher_authenticated"] is False
    assert assurance["semantic_support_verified"] is False
