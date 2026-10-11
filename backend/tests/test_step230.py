"""Step 230: real HTML quotation-origin guard for bounded claim mode.

HTML is parsed through the real allowlisted reader, with a fake only at
the socket/response transport boundary. Tests are not genuine publisher HTTPS.
"""
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.api.reality_state import RealityStateResponse
from backend.app.main import app
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.allowlisted_https_source_reader import (
    AllowlistedHttpsSourceReader, _decode_observed_content,
)
from backend.app.reality.independent_source_text_assurance import IndependentSourceTextAssurance
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator

URL = "https://www.python.org/downloads/release/python-3130/"
QUOTE = "Python 3.13.0 is a stable release."
NOW = datetime.now(timezone.utc)


def html_reader(markup: str, mime: str = "text/html; charset=utf-8"):
    wire = ("<html><body>" + markup + "</body></html>").encode("utf-8")
    class Response:
        status = 200
        def getheader(self, name, default=None):
            return {"Content-Type": mime, "Content-Length": str(len(wire))}.get(name, default)
        def read(self, n):
            return wire[:n]

    class Transport:
        def __init__(self, *args, **kwargs):
            pass
        def request(self, *args, **kwargs):
            pass
        def getresponse(self):
            return Response()
        def close(self):
            pass

    return AllowlistedHttpsSourceReader(
        [URL], clock=lambda: NOW, connection_factory=Transport
    )


def _run(markup, *, claim=True):
    reader = html_reader(markup)
    deps = replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(reader),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
    )
    return build_reality_state_from_evidence(
        "Is Python 3.13.0 a stable release?",
        [{"uri": URL, "content": QUOTE}],
        entity="Python 3.13.0",
        freshness_max_age_seconds=3600,
        require_independent_source_text_match=True,
        require_claim_alignment=claim,
        claim_text=QUOTE if claim else None,
        dependencies=deps,
    )


@pytest.mark.parametrize("markup", [
    "<blockquote><p>" + QUOTE + "</p></blockquote>",
    "<blockquote>" + QUOTE + "</blockquote>",
    "<p><q>" + QUOTE + "</q></p>",
    "<blockquote><p><strong>" + QUOTE + "</strong></p></blockquote>",
    "<div><blockquote><span>" + QUOTE + "</span></blockquote></div>",
])
def test_explicit_html_quote_as_sole_complete_source_unit_is_refused(markup):
    observed = html_reader(markup)(URL)
    assert observed["content"] == QUOTE
    assert sha256(QUOTE.encode()).hexdigest() in observed["observed_quote_unit_sha256"]
    state = _run(markup)
    assert state["status"] == "uncertain"
    source = state["evidence"]["independent_source_text_assurance"]["sources"][0]
    assert source["reason"] == "original_source_quoted_html_unit"
    assert source["source_quote_context_status"] == "quoted_source_unit"
    assert source["capture_sha256"] is None
    assert state["evidence"]["claim_alignment"]["status"] == "insufficient"
    RealityStateResponse.model_validate(state)


@pytest.mark.parametrize("markup", [
    "<p>" + QUOTE + "</p>",
    "<h2>" + QUOTE + "</h2>",
    "<div><p>" + QUOTE + "</p><p>General information.</p></div>",
])
def test_complete_nonquoted_original_statement_stays_eligible(markup):
    reader_out = html_reader(markup)(URL)
    assert reader_out["observed_quote_unit_sha256"] == []
    state = _run(markup)
    assert state["status"] == "supported"
    row = state["evidence"]["independent_source_text_assurance"]["sources"][0]
    assert row["source_quote_context_status"] == "no_matching_html_quote_unit"
    assert state["evidence"]["claim_alignment"]["status"] == "aligned"
    assert state["evidence"]["claim_alignment"]["semantic_support_verified"] is False


def test_quote_origin_stays_present_for_legacy_text_presence_mode():
    quote = _run("<blockquote><p>" + QUOTE + "</p></blockquote>", claim=False)
    assert quote["evidence"]["independent_source_text_assurance"]["status"] == "exact_text_observed"
    row = quote["evidence"]["independent_source_text_assurance"]["sources"][0]
    assert "source_quote_context_status" not in row
    assert "claim_alignment" not in quote["evidence"]


@pytest.mark.parametrize("bad_metadata", [None, {}, {"observed_quote_unit_sha256": "not-list"}, {"observed_quote_unit_sha256": ["bogus"]}])
def test_claim_mode_without_valid_backend_quote_metadata_fails_closed(bad_metadata):
    doc = {"uri": URL, "content": QUOTE}
    data = {
        "uri": URL, "content": QUOTE,
        "capture_sha256": sha256(QUOTE.encode()).hexdigest(),
        "capture_observed_at": NOW.isoformat().replace("+00:00", "Z"),
    }
    if bad_metadata:
        data.update(bad_metadata)
    deps = replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(lambda uri: data),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
    )
    state = build_reality_state_from_evidence(
        "Check quote scope", [doc], entity="Python 3.13.0",
        freshness_max_age_seconds=3600,
        require_independent_source_text_match=True, require_claim_alignment=True,
        claim_text=QUOTE, dependencies=deps,
    )
    assert state["status"] == "uncertain"
    assert state["evidence"]["independent_source_text_assurance"]["sources"][0]["reason"] == "independent_reader_quote_context_unavailable"


def test_actual_fastapi_route_refuses_quote_without_client_overrides(monkeypatch):
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([URL]))
    reader = html_reader("<blockquote><p>" + QUOTE + "</p></blockquote>")
    real_call = AllowlistedHttpsSourceReader.__call__
    monkeypatch.setattr(
        AllowlistedHttpsSourceReader, "__call__",
        lambda self, uri: real_call(reader, uri)
    )
    data = {
        "task": "Check publisher assertion",
        "entity": "Python 3.13.0",
        "documents": [{"uri": URL, "content": QUOTE}],
        "require_independent_source_text_match": True,
        "require_claim_alignment": True,
        "claim_text": QUOTE,
        "freshness_max_age_seconds": 3600,
    }
    with TestClient(app) as client:
        response = client.post("/api/v1/reality-state/evidence", json=data)
        assert response.status_code == 200
        assert response.json()["status"] == "uncertain"
        assert response.json()["evidence"]["independent_source_text_assurance"]["sources"][0]["reason"] == "original_source_quoted_html_unit"
        data["documents"][0]["observed_quote_unit_sha256"] = []
        assert client.post("/api/v1/reality-state/evidence", json=data).status_code == 422


def test_hidden_quotation_cannot_become_visible_quote_metadata():
    source = html_reader(
        "<blockquote hidden><p>" + QUOTE + "</p></blockquote>"
        "<h2>Python 3.13.0 is generally available.</h2>"
    )(URL)
    assert QUOTE not in source["content"]
    assert source["observed_quote_unit_sha256"] == []


def test_original_html_text_reader_preserves_legacy_quoted_visible_text():
    markup = "<p>Introduction.</p><blockquote><p>" + QUOTE + "</p></blockquote>"
    original = _decode_observed_content(
        ("<html><body>" + markup + "</body></html>").encode(), "text/html"
    )
    latest = html_reader(markup)(URL)["content"]
    assert original == latest
    assert QUOTE in original
