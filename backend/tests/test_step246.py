"""Step246 real local authenticated API and mock-reader recheck adversarial suite.

Mocked publisher snapshots exercise controlled changes; the separate live
canary genuinely reads real HTTPS twice and does NOT certify publisher truth.
"""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.cli import EXIT_ABSTAIN, EXIT_BOUNDED, EXIT_REFUSED, run
from backend.app.integrations.cited_answer_client import check_cited_answer_with_api
from backend.app.integrations.source_recheck import (
    SourceRecheck, RECHECK_ABSTAINED, recheck_cited_answer_with_api,
)
from backend.app.main import app
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader

SOURCE = "https://www.python.org/downloads/release/python-3130/"
IANA = "https://www.iana.org/domains/reserved"
TOKEN = "step246-local-operator-only-test-authentication-token"
CLAIM = "Python 3.13.0 is a stable release."
POSITIVE = "This is the stable release of Python 3.13.0"
NEGATIVE = "Python 3.13.0 is not a stable release."


def req():
    return OriginalSourceClaimRequest(
        claim_text=CLAIM, entity="Python 3.13.0",
        source_uri=SOURCE, freshness_max_age_seconds=3600,
    )


def snapshot(body=POSITIVE, *, time=None, uri=SOURCE, quote_hashes=None):
    return {
        "uri": uri, "content": body,
        "capture_sha256": sha256(body.encode("utf-8")).hexdigest(),
        "capture_observed_at": (
            time or datetime.now(timezone.utc)
        ).isoformat().replace("+00:00", "Z"),
        "observed_quote_unit_sha256": quote_hashes or [],
    }


def argv(*sources, live=True, recheck=True, quotes=False):
    args = ["--claim", CLAIM, "--entity", "Python 3.13.0"]
    for uri in sources or (SOURCE,):
        args += ["--source", uri]
    if live:
        args.append("--live")
    if recheck:
        args.append("--recheck")
    if quotes:
        args.append("--include-untrusted-quotes")
    return args


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("ARL_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("ARL_PILOT_BEARER_TOKEN", TOKEN)
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([SOURCE, IANA]))
    original = snapshot()
    next_capture = snapshot()
    state = {"calls": 0, "captures": [original, next_capture]}

    def reader(self, uri):
        assert uri == SOURCE
        idx = state["calls"]
        state["calls"] += 1
        if idx >= len(state["captures"]):
            raise RuntimeError("unexpected third source fetch")
        item = state["captures"][idx]
        if isinstance(item, Exception):
            raise item
        return deepcopy(item)

    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", reader)
    return state


def assert_safe(result):
    for flag in (
        "factual_truth_verified", "publisher_authorship_verified",
        "historical_receipt_authenticated", "independent_publisher_ownership_verified",
        "automatic_monitoring_enabled",
    ):
        assert getattr(result, flag) is False


def assert_abstain(result):
    assert result.status == "abstain"
    assert result.answer_text == RECHECK_ABSTAINED
    assert result.previous is None
    assert result.current is None
    assert result.previous_decision is None
    assert result.current_decision is None
    assert result.may_use_current_as_bounded_evidence is False
    assert SOURCE not in repr(result)
    assert POSITIVE not in repr(result)
    assert_safe(result)


def test_actual_two_authenticated_source_captures_unchanged(provider):
    with TestClient(app) as client:
        previous = check_cited_answer_with_api(client, TOKEN, req())
        result = recheck_cited_answer_with_api(client, TOKEN, req(), previous)
    assert provider["calls"] == 2
    assert result.status == "capture_unchanged"
    assert result.current_decision == "bounded_source_support"
    assert result.previous_decision == "bounded_source_support"
    assert result.may_use_current_as_bounded_evidence is True
    assert result.current.source_uri == result.previous.source_uri == SOURCE
    assert result.current.source_quote_sha256 == result.previous.source_quote_sha256
    assert_safe(result)
    with pytest.raises(FrozenInstanceError):
        result.status = "abstain"


def test_capture_changed_but_same_bounded_quote(provider):
    provider["captures"][1] = snapshot(POSITIVE + "\nAdditional page metadata")
    with TestClient(app) as client:
        previous = check_cited_answer_with_api(client, TOKEN, req())
        result = recheck_cited_answer_with_api(client, TOKEN, req(), previous)
    assert result.status == "capture_changed_statement_unchanged"
    assert result.previous.source_capture_sha256 != result.current.source_capture_sha256
    assert result.previous.source_quote_sha256 == result.current.source_quote_sha256
    assert result.may_use_current_as_bounded_evidence is True
    assert provider["calls"] == 2
    assert_safe(result)


def test_real_bounded_statement_changes_direction(provider):
    provider["captures"][1] = snapshot(NEGATIVE)
    with TestClient(app) as client:
        previous = check_cited_answer_with_api(client, TOKEN, req())
        result = recheck_cited_answer_with_api(client, TOKEN, req(), previous)
    assert provider["calls"] == 2
    assert result.status == "bounded_statement_changed"
    assert result.previous_decision == "bounded_source_support"
    assert result.current_decision == "bounded_source_contradiction"
    assert result.may_use_current_as_bounded_evidence is False
    assert result.previous.original_source_quote == POSITIVE
    assert result.current.original_source_quote == NEGATIVE
    assert_safe(result)


def test_bounded_statement_changes_opposite_direction(provider):
    # Retain the already-created baseline capture time. Creating a NEW first
    # capture after the fixture's second one would reverse chronology.
    baseline_time = datetime.fromisoformat(
        provider["captures"][0]["capture_observed_at"].replace("Z", "+00:00")
    )
    provider["captures"][0] = snapshot(NEGATIVE, time=baseline_time)
    with TestClient(app) as client:
        previous = check_cited_answer_with_api(client, TOKEN, req())
        result = recheck_cited_answer_with_api(client, TOKEN, req(), previous)
    assert result.status == "bounded_statement_changed"
    assert result.previous_decision == "bounded_source_contradiction"
    assert result.current_decision == "bounded_source_support"
    assert result.may_use_current_as_bounded_evidence is True
    assert provider["calls"] == 2


@pytest.mark.parametrize("defect", [
    "source_down", "unrelated", "invalid_uri", "quoted", "stale",
    "bad_digest", "duplicate_statement",
])
def test_second_source_failure_suppresses_previous_and_current_citations(provider, defect):
    if defect == "source_down":
        provider["captures"][1] = OSError("SECRET sentinel must not leak")
    elif defect == "unrelated":
        provider["captures"][1] = snapshot("This website discusses unrelated topics.")
    elif defect == "invalid_uri":
        provider["captures"][1] = snapshot(uri=IANA)
    elif defect == "quoted":
        provider["captures"][1] = snapshot(
            quote_hashes=[sha256(POSITIVE.encode()).hexdigest()]
        )
    elif defect == "stale":
        provider["captures"][1] = snapshot(
            time=datetime.now(timezone.utc) - timedelta(hours=4)
        )
    elif defect == "bad_digest":
        provider["captures"][1]["capture_sha256"] = "not-a-sha"
    elif defect == "duplicate_statement":
        provider["captures"][1] = snapshot(POSITIVE + "\n" + POSITIVE)
    with TestClient(app) as client:
        previous = check_cited_answer_with_api(client, TOKEN, req())
        result = recheck_cited_answer_with_api(client, TOKEN, req(), previous)
    assert_abstain(result)
    assert provider["calls"] == 2
    assert "SECRET sentinel" not in repr(result)


@pytest.mark.parametrize("invalid", [
    "wrong_binding", "wrong_uri", "invalid_quote_sha", "quote_mutated",
    "fake_supported_flag", "fake_truth_flag", "fake_answer_text",
    "fake_reason", "invalid_capture_sha", "future_capture",
    "impossible_grammar",
])
def test_forged_baseline_fails_before_any_new_source_fetch(provider, invalid):
    with TestClient(app) as client:
        previous = check_cited_answer_with_api(client, TOKEN, req())
        c = previous.citation
        if invalid == "wrong_binding":
            previous = replace(previous, request_binding_sha256="0"*64)
        elif invalid == "wrong_uri":
            previous = replace(previous, citation=replace(c, source_uri=IANA))
        elif invalid == "invalid_quote_sha":
            previous = replace(previous, citation=replace(c, source_quote_sha256="0"*64))
        elif invalid == "quote_mutated":
            previous = replace(previous, citation=replace(c, original_source_quote=NEGATIVE))
        elif invalid == "fake_supported_flag":
            previous = replace(previous, may_use_as_bounded_evidence=False)
        elif invalid == "fake_truth_flag":
            previous = replace(previous, factual_truth_verified=True)
        elif invalid == "fake_answer_text":
            previous = replace(previous, answer_text="It is objectively true")
        elif invalid == "fake_reason":
            previous = replace(previous, reason_code="api_unavailable_or_invalid")
        elif invalid == "invalid_capture_sha":
            previous = replace(previous, citation=replace(c, source_capture_sha256="nothex"))
        elif invalid == "future_capture":
            future = (datetime.now(timezone.utc)+timedelta(hours=4)).isoformat().replace("+00:00","Z")
            previous = replace(previous, citation=replace(c, source_capture_observed_at=future))
        elif invalid == "impossible_grammar":
            t = "Maybe Python 3.13.0 is an interesting application"
            previous = replace(previous, citation=replace(
                c, original_source_quote=t, source_quote_sha256=sha256(t.encode()).hexdigest(),
            ))
        before = provider["calls"]
        result = recheck_cited_answer_with_api(client, TOKEN, req(), previous)
    assert_abstain(result)
    assert provider["calls"] == before == 1


def test_baseline_can_be_old_but_never_claimed_current_or_authentic(provider):
    with TestClient(app) as client:
        previous = check_cited_answer_with_api(client, TOKEN, req())
        old = (datetime.now(timezone.utc)-timedelta(days=10)).isoformat().replace("+00:00","Z")
        prior = replace(previous, citation=replace(previous.citation, source_capture_observed_at=old))
        result = recheck_cited_answer_with_api(client, TOKEN, req(), prior)
    assert result.status == "capture_unchanged"
    assert result.historical_receipt_authenticated is False
    assert result.current is not None
    assert provider["calls"] == 2


def test_same_capture_digest_and_changed_quote_fails_closed(provider):
    provider["captures"][1] = snapshot(NEGATIVE)
    # Mock attack: identical raw digest despite different source content.
    provider["captures"][1]["capture_sha256"] = provider["captures"][0]["capture_sha256"]
    with TestClient(app) as client:
        previous = check_cited_answer_with_api(client, TOKEN, req())
        result = recheck_cited_answer_with_api(client, TOKEN, req(), previous)
    assert_abstain(result)
    assert provider["calls"] == 2


def test_backwards_capture_time_refuses(provider):
    t = datetime.now(timezone.utc)
    provider["captures"][0] = snapshot(time=t)
    provider["captures"][1] = snapshot(time=t - timedelta(seconds=40))
    with TestClient(app) as client:
        previous = check_cited_answer_with_api(client, TOKEN, req())
        result = recheck_cited_answer_with_api(client, TOKEN, req(), previous)
    assert_abstain(result)
    assert provider["calls"] == 2


def test_bad_or_missing_bearer_does_not_disclose_source_on_recheck(provider):
    with TestClient(app) as client:
        previous = check_cited_answer_with_api(client, TOKEN, req())
        before = provider["calls"]
        result = recheck_cited_answer_with_api(client, TOKEN + "bad", req(), previous)
    assert_abstain(result)
    assert provider["calls"] == before == 1


def test_cli_recheck_renders_two_safe_digest_only_observations(provider):
    code, data = run(argv(SOURCE))
    assert code == EXIT_BOUNDED
    assert data["scope"] == "two_observations_of_one_original_source"
    assert data["recheck_status"] == "capture_unchanged"
    assert data["may_use_as_bounded_evidence"] is True
    assert data["historical_receipt_authenticated"] is False
    assert data["automatic_monitoring_enabled"] is False
    assert [x["role"] for x in data["observations"]] == ["previous", "current"]
    assert "untrusted_original_source_quote" not in json.dumps(data)
    assert TOKEN not in json.dumps(data)
    assert provider["calls"] == 2


def test_cli_recheck_quote_optin_is_labeled_untrusted_data(provider):
    code, data = run(argv(SOURCE, quotes=True))
    assert code == EXIT_BOUNDED
    assert [x["untrusted_original_source_quote"] for x in data["observations"]] == [POSITIVE, POSITIVE]
    assert data["factual_truth_verified"] is False
    assert provider["calls"] == 2


def test_cli_recheck_no_live_refuses_without_any_fetch(provider):
    code, report = run(argv(SOURCE, live=False))
    assert (code, report) == (EXIT_REFUSED, None)
    assert provider["calls"] == 0


def test_cli_two_host_recheck_is_refused_no_eager_source_reads(provider):
    code, report = run(argv(SOURCE, IANA))
    assert (code, report) == (EXIT_REFUSED, None)
    assert provider["calls"] == 0


def test_cli_recheck_unapproved_source_does_not_fetch(provider):
    code, report = run(argv("https://go.dev/dl/"))
    assert (code, report) == (EXIT_REFUSED, None)
    assert provider["calls"] == 0


def test_cli_recheck_first_source_unavailable_never_makes_second_request(provider):
    provider["captures"][0] = RuntimeError("SECRET first source")
    code, report = run(argv(SOURCE, quotes=True))
    assert code == EXIT_ABSTAIN
    assert report["recheck_status"] == "abstain"
    assert report["observations"] == []
    assert SOURCE not in json.dumps(report)
    assert POSITIVE not in json.dumps(report)
    assert provider["calls"] == 1


def test_cli_recheck_changed_claim_with_current_contradiction_is_not_support(provider):
    provider["captures"][1] = snapshot(NEGATIVE)
    code, result = run(argv(SOURCE))
    assert code == EXIT_BOUNDED
    assert result["recheck_status"] == "bounded_statement_changed"
    assert result["may_use_as_bounded_evidence"] is False
    assert result["previous_decision"] == "bounded_source_support"
    assert result["current_decision"] == "bounded_source_contradiction"


def test_recheck_rejects_invalid_previous_type_without_network(provider):
    with TestClient(app) as client:
        result = recheck_cited_answer_with_api(client, TOKEN, req(), {"fake": "prior"})
    assert_abstain(result)
    assert provider["calls"] == 0


def test_recheck_unverified_grammar_does_not_promote_snapshot(provider):
    invalid_request = OriginalSourceClaimRequest(
        claim_text="Python 3.13.0 is ready for every application.",
        entity="Python 3.13.0", source_uri=SOURCE,
    )
    with TestClient(app) as client:
        prior = check_cited_answer_with_api(client, TOKEN, invalid_request)
        # An otherwise grammatical-but-unsupported claim may take ONE
        # original-source read before its first evaluation abstains.
        baseline_reads = provider["calls"]
        r = recheck_cited_answer_with_api(client, TOKEN, invalid_request, prior)
    assert prior.decision == "abstain"
    assert_abstain(r)
    # Recheck MUST NOT fetch again after the first result lacks a citation.
    assert baseline_reads == 1
    assert provider["calls"] == baseline_reads
