"""Step 222: real-source smoke policy tests, isolated from public networking."""

from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json

import pytest

from backend.app.evaluation import live_source_quality_smoke as smoke
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader


def capture(content=None, *, uri=smoke.PUBLISHER_URL, sha=None, observed=None):
    if content is None:
        content = (
            "<unpublished PRIVATE-RAW-RESPONSE-MUST-NOT-LEAK> "
            + smoke.EXPECTED_EXCERPT
            + " "
            + smoke.HISTORICAL_DATE_TEXT
        )
    return {
        "uri": uri,
        "content": content,
        "capture_sha256": sha if sha is not None else sha256(content.encode()).hexdigest(),
        "capture_observed_at": observed or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@pytest.fixture
def configured_fake(monkeypatch):
    monkeypatch.setenv(
        "ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([smoke.PUBLISHER_URL])
    )
    requested = []
    def fake_read(self, uri):
        requested.append(uri)
        return capture()
    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", fake_read)
    return requested


def test_opt_in_real_source_smoke_reaches_real_http_api_contract_with_fake_network(configured_fake):
    # Transport fake is explicitly TEST-ONLY; live GitHub workflow exercises
    # the real socket/DNS/TLS with the fixed original publisher URI.
    report = smoke.run_live_smoke()
    assert configured_fake == [smoke.PUBLISHER_URL] * 3
    assert report["scenario_count"] == 2
    assert report["legitimate_excerpt"]["reality_state"] == "supported"
    assert report["legitimate_excerpt"]["source_text_assurance"] == "exact_text_observed"
    assert report["forged_same_url_excerpt"]["reality_state"] == "uncertain"
    assert report["forged_same_url_excerpt"]["reason"] == "submitted_text_not_in_observed_content"
    assert report["forged_supported"] == 0
    assert report["publisher_authenticated"] is False
    assert report["semantic_support_verified"] is False
    assert "PRIVATE-RAW-RESPONSE-MUST-NOT-LEAK" not in json.dumps(report)


def test_live_smoke_writes_audit_only_not_original_page(tmp_path, configured_fake):
    target = tmp_path / "audit.json"
    assert smoke.main(["--live", "--output", str(target)]) == 0
    report = json.loads(target.read_text())
    assert report["scenario_count"] == 2
    assert "PRIVATE-RAW-RESPONSE-MUST-NOT-LEAK" not in target.read_text()
    assert target.read_text() == json.dumps(report, indent=2, sort_keys=True) + "\n"


def test_no_network_by_default_even_when_reader_configured(configured_fake):
    with pytest.raises(SystemExit):
        smoke.main([])
    assert configured_fake == []


def test_no_operator_allowlist_fails_closed_before_network(monkeypatch):
    monkeypatch.delenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", raising=False)
    def forbid_read(self, uri):
        raise AssertionError("network must not be called")
    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", forbid_read)
    with pytest.raises(RuntimeError, match="operator-configured"):
        smoke.run_live_smoke()


@pytest.mark.parametrize("wrong", [
    ["https://www.python.org/downloads/"],
    [smoke.PUBLISHER_URL, "https://www.python.org/"],
])
def test_extra_or_wrong_allowlist_cannot_expand_canary_scope(monkeypatch, wrong):
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps(wrong))
    calls = []
    monkeypatch.setattr(
        AllowlistedHttpsSourceReader, "__call__",
        lambda self, uri: calls.append(uri),
    )
    with pytest.raises(RuntimeError, match="exactly the fixed"):
        smoke.run_live_smoke()
    assert calls == []


@pytest.mark.parametrize("invalid", [
    capture(content="This is the stable release of Python 3.13.0"),
    capture(content="Release date: Oct. 7, 2024"),
    capture(uri="https://other.example.test"),
    capture(sha="not-a-digest"),
    capture(observed="2026-01-01T00:00:00Z"),
    capture(observed=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat().replace("+00:00", "Z")),
])
def test_live_capture_integrity_must_hold_before_api_requests(invalid, monkeypatch):
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([smoke.PUBLISHER_URL]))
    calls = []
    def fake_read(self, uri):
        calls.append(uri)
        return invalid
    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", fake_read)
    with pytest.raises(RuntimeError):
        smoke.run_live_smoke()
    assert calls == [smoke.PUBLISHER_URL]


def test_bad_observer_failure_is_sanitized_and_no_artifact(tmp_path, configured_fake, monkeypatch, capsys):
    target = tmp_path / "report.json"
    def broken_read(self, uri):
        raise RuntimeError("sensitive exception mentioning credentials")
    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", broken_read)
    assert smoke.main(["--live", "--output", str(target)]) == 1
    assert not target.exists()
    assert "credentials" not in capsys.readouterr().out


def test_positive_capture_metadata_and_source_failure_labels_are_not_trust_flags(configured_fake):
    report = smoke.run_live_smoke()
    assert len(report["capture"]["capture_sha256"]) == 64
    assert report["real_world_factual_accuracy_established"] is False
    assert report["corpus_type"] == "live_original_https_page_not_publisher_authenticated"


def test_reader_accepts_single_bounded_gzip_html_and_hashes_wire_bytes():
    import gzip
    from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

    html = b"<html><body><p>This is the stable release of Python 3.13.0</p></body></html>"
    wire = gzip.compress(html)
    class Response:
        status = 200
        def getheader(self, key, default=None):
            return {
                "Content-Type": "text/html; charset=utf-8",
                "Content-Encoding": "gzip",
                "Content-Length": str(len(wire)),
            }.get(key, default)
        def read(self, count):
            return wire[:count]
    class Connection:
        def __init__(self, *args, **kwargs):
            pass
        def request(self, *args, **kwargs):
            pass
        def getresponse(self):
            return Response()
        def close(self):
            pass
    reader = AllowlistedHttpsSourceReader(
        [smoke.PUBLISHER_URL], connection_factory=Connection,
    )
    observed = reader(smoke.PUBLISHER_URL)
    assert observed["content"] == smoke.EXPECTED_EXCERPT
    assert observed["capture_sha256"] == sha256(wire).hexdigest()


def test_bounded_gzip_decoder_rejects_bombs_truncation_and_extra_members():
    import gzip
    from backend.app.reality.allowlisted_https_source_reader import _bounded_gzip_decode

    raw = b"source evidence text"
    wire = gzip.compress(raw)
    assert _bounded_gzip_decode(wire, limit=len(raw)) == raw
    with pytest.raises(ValueError, match="exceeds byte limit"):
        _bounded_gzip_decode(gzip.compress(b"X" * 100000), limit=100)
    with pytest.raises(ValueError, match="invalid or incomplete"):
        _bounded_gzip_decode(wire[:-3], limit=1000)
    with pytest.raises(ValueError, match="invalid or incomplete"):
        _bounded_gzip_decode(wire + gzip.compress(b"second"), limit=1000)
    with pytest.raises(ValueError, match="invalid or incomplete"):
        _bounded_gzip_decode(wire + b"trailing", limit=1000)
    with pytest.raises(ValueError, match="invalid or incomplete"):
        _bounded_gzip_decode(b"not gzip", limit=1000)
