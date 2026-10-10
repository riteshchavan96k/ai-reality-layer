"""Step 226 controlled tests. These fixtures do NOT contact real publishers."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest

from backend.app.evaluation import multi_publisher_live_smoke as smoke
from backend.app.reality.allowlisted_https_source_reader import (
    AllowlistedHttpsSourceReader,
)

URLS = [item["url"] for item in smoke.PUBLISHERS]


@pytest.fixture
def approved_network(monkeypatch):
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps(URLS))
    calls = []
    def fake_get(self, uri):
        calls.append(uri)
        source = next(s for s in smoke.PUBLISHERS if s["url"] == uri)
        # This text is **reviewer-authored test-only**, not fetched publisher
        # bytes. Live workflow separately exercises real DNS/TLS/TCP/HTTP.
        text = ("\n".join(source["anchors"]) + "\nIndependent source fixture.")
        return {
            "uri": uri,
            "content": text,
            "capture_sha256": sha256(text.encode()).hexdigest(),
            "capture_observed_at": (
                datetime.now(timezone.utc)
                .isoformat().replace("+00:00", "Z")
            ),
        }
    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", fake_get)
    return calls


def test_two_publisher_strict_end_to_end_api_with_injected_fake_transport(approved_network):
    report = smoke.run_live_smoke()
    assert len(approved_network) == 10  # 2 preflights, 4 one-source, 4 mixed
    assert approved_network.count(URLS[0]) == 5
    assert approved_network.count(URLS[1]) == 5
    assert report["publisher_count"] == 2
    assert report["scenario_count"] == 6
    assert report["authentic_cases_supported"] == 3
    assert report["forged_cases_supported"] == 0
    assert report["conservative_refusals"] == 3
    assert len(report["captures"]) == 2
    assert report["population_factual_accuracy_established"] is False
    assert report["publisher_authenticated"] is False
    assert report["semantic_support_verified"] is False
    assert {c["scenario_id"] for c in report["cases"]} == {
        "python-org-release-authentic", "python-org-release-forged",
        "iana-reserved-domains-authentic", "iana-reserved-domains-forged",
        "both-publishers-authentic", "mixed-one-forged",
    }
    assert not any(
        "fixture" in str(capture) for capture in report["captures"].values()
    )


def test_approved_live_cli_audit_contains_only_public_metadata_and_decisions(
    approved_network, capsys, tmp_path
):
    path = tmp_path / "step226-audit.json"
    assert smoke.main(["--live", "--output", str(path)]) == 0
    report = json.loads(path.read_text())
    assert report["publisher_count"] == 2
    assert report["scenario_count"] == 6
    assert path.read_text() == json.dumps(report, indent=2, sort_keys=True) + "\n"
    assert "Independent source fixture" not in path.read_text()
    assert "Independent source fixture" not in capsys.readouterr().out


def test_no_network_by_default_even_when_operator_has_allowlisted(approved_network):
    with pytest.raises(SystemExit):
        smoke.main([])
    assert approved_network == []


def test_unconfigured_reader_fails_before_network(monkeypatch):
    monkeypatch.delenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", raising=False)
    seen = []
    monkeypatch.setattr(
        AllowlistedHttpsSourceReader, "__call__",
        lambda self, uri: seen.append(uri),
    )
    with pytest.raises(smoke.SmokeGateError, match="operator_https_reader_required"):
        smoke.run_live_smoke()
    assert seen == []


@pytest.mark.parametrize("allowlist", [
    [URLS[0]],
    [URLS[1]],
    list(URLS) + ["https://www.iana.org/"],
])
def test_mismatched_or_expanded_operator_allowlist_fails_before_network(
    monkeypatch, allowlist
):
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps(allowlist))
    seen = []
    monkeypatch.setattr(
        AllowlistedHttpsSourceReader, "__call__",
        lambda self, uri: seen.append(uri),
    )
    with pytest.raises(smoke.SmokeGateError, match="exact_two_publisher_allowlist_required"):
        smoke.run_live_smoke()
    assert seen == []


@pytest.mark.parametrize("bad", [
    {"uri": "https://another.example", "content": "irrelevant"},
    {"content": "missing uri"},
    {"capture_sha256": "invalid"},
    {"capture_observed_at": "bad"},
    {"capture_observed_at": "2050-01-01T00:00:00Z"},
    {"capture_observed_at": "2024-01-01T00:00:00Z"},
    {"content": "one anchor only"},
])
def test_bad_independent_capture_refuses_quality_scorecard(bad):
    source = smoke.PUBLISHERS[0]
    content = "\n".join(source["anchors"])
    baseline = {
        "uri": source["url"],
        "content": content,
        "capture_sha256": sha256(content.encode()).hexdigest(),
        "capture_observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    baseline.update(bad)
    with pytest.raises(smoke.SmokeGateError):
        smoke._check_receipt(source, baseline)


def test_capture_boundary_fails_for_stale_or_future_utc():
    source = smoke.PUBLISHERS[1]
    body = "\n".join(source["anchors"])
    baseline = {
        "uri": source["url"],
        "content": body,
        "capture_sha256": sha256(body.encode()).hexdigest(),
    }
    for delta in (timedelta(minutes=-8), timedelta(minutes=8)):
        capture = dict(baseline)
        capture["capture_observed_at"] = (
            datetime.now(timezone.utc) + delta
        ).isoformat().replace("+00:00", "Z")
        with pytest.raises(smoke.SmokeGateError, match="capture_timestamp_out_of_live_window"):
            smoke._check_receipt(source, capture)


def test_live_network_failure_is_sanitized_and_no_file_written(
    approved_network, monkeypatch, capsys, tmp_path
):
    def bad_reader(self, uri):
        raise RuntimeError("secret-token-here-private-http-response")
    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", bad_reader)
    dest = tmp_path / "audit.json"
    assert smoke.main(["--live", "--output", str(dest)]) == 1
    assert not dest.exists()
    text = capsys.readouterr().out
    assert "secret-token" not in text and "private-http-response" not in text


def test_declared_original_sources_have_two_distinct_approved_domains():
    assert len(smoke.APPROVED_URLS) == 2
    assert URLS[0].startswith("https://www.python.org/")
    assert URLS[1].startswith("https://www.iana.org/")
    assert all(source["positive"] in source["anchors"] for source in smoke.PUBLISHERS)
    assert all(source["forged"] not in source["anchors"] for source in smoke.PUBLISHERS)


def test_public_api_two_sources_cannot_claim_semantic_truth(approved_network):
    report = smoke.run_live_smoke()
    cases = {case["scenario_id"]: case for case in report["cases"]}
    assert cases["both-publishers-authentic"]["verified_source_count"] == 2
    assert cases["mixed-one-forged"]["verified_source_count"] == 1
    assert cases["mixed-one-forged"]["reality_state"] == "uncertain"
