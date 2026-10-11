"""Step 229 bounded source-wide counterstatement guard regression tests.

All injected backend-observer bodies are synthetic. Genuine publisher
DNS/TLS/HTTPS checks remain separate mandatory GitHub Actions workflows.
"""

from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.independent_source_text_assurance import IndependentSourceTextAssurance
from backend.app.reality.source_counterstatement_guard import (
    MAX_OBSERVED_SOURCE_CHARS,
    has_bounded_source_counterstatement,
)
from backend.app.reality.claim_assertion_alignment import evaluate_claim_alignment
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.allowlisted_https_source_reader import (
    AllowlistedHttpsSourceReader, _decode_observed_content,
)

URL = "https://www.python.org/downloads/release/python-3130/"
SOURCE_RELEASE = "Python 3.13.0 was released on October 7, 2024."
NEGATED_RELEASE = "Python 3.13.0 was not released on October 7, 2024."
DIFFERENT_DATE = "Python 3.13.0 was released on January 1, 1900."
STABLE = "This is the stable release of Python 3.13.0"
NEGATED_STABLE = "Python 3.13.0 is not a stable release."
NOW = datetime.now(timezone.utc)


def _reader(source_text):
    return lambda url: {
        "uri": url,
        "content": source_text,
        "capture_sha256": sha256(source_text.encode()).hexdigest(),
        "capture_observed_at": NOW.isoformat().replace("+00:00", "Z"),
        "observed_quote_unit_sha256": [],
    }


def _state(excerpt=SOURCE_RELEASE, observed=None, claim=None, *, claim_mode=True):
    observed = excerpt if observed is None else observed
    deps = replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(_reader(observed)),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
    )
    return build_reality_state_from_evidence(
        "Evaluate original-source statement with independent cross-unit checks",
        [{"uri": URL, "content": excerpt}],
        entity="Python 3.13.0",
        require_independent_source_text_match=True,
        require_claim_alignment=claim_mode,
        claim_text=(claim or excerpt) if claim_mode else None,
        freshness_max_age_seconds=3600,
        dependencies=deps,
    )


@pytest.mark.parametrize("observed", [
    SOURCE_RELEASE + "\n" + NEGATED_RELEASE,
    NEGATED_RELEASE + "\n" + SOURCE_RELEASE,
    SOURCE_RELEASE + "\n" + DIFFERENT_DATE,
    DIFFERENT_DATE + "\n" + SOURCE_RELEASE,
    "Header.\n" + SOURCE_RELEASE + "\n" + NEGATED_RELEASE + "\nFootnote.",
    SOURCE_RELEASE + "\nOther fact.\n" + NEGATED_RELEASE,
])
def test_cross_unit_counterstatement_refuses_claim_support(observed):
    result = _state(observed=observed)
    assert result["status"] == "uncertain"
    audit = result["evidence"]["independent_source_text_assurance"]
    assert audit["status"] == "unverified"
    assert audit["sources"][0]["reason"] == "independent_source_explicit_counterstatement"
    assert audit["sources"][0]["assertion_context_status"] == "unverified"
    assert audit["sources"][0]["source_counterstatement_status"] == "counterstatement_observed"
    assert audit["sources"][0]["capture_sha256"] is None
    assert audit["sources"][0]["capture_observed_at"] is None
    assert result["evidence"]["claim_alignment"]["status"] == "insufficient"


@pytest.mark.parametrize("prefix", ["It is false that ", "It is untrue that "])
def test_repeated_excerpt_in_denial_is_already_refused_by_step228(prefix):
    result = _state(observed=SOURCE_RELEASE + "\n" + prefix + SOURCE_RELEASE)
    row = result["evidence"]["independent_source_text_assurance"]["sources"][0]
    assert result["status"] == "uncertain"
    assert row["reason"] == "excerpt_not_unique_standalone_source_unit"
    assert row["source_counterstatement_status"] == "unverified"
    assert result["evidence"]["claim_alignment"]["status"] == "insufficient"


@pytest.mark.parametrize("source,claim,opposite", [
    (SOURCE_RELEASE, SOURCE_RELEASE, NEGATED_RELEASE),
    (STABLE, "Python 3.13.0 is a stable release.", NEGATED_STABLE),
])
def test_source_wide_explicit_negation_covers_both_bounded_grammars(source, claim, opposite):
    result = _state(source, source + "\n" + opposite, claim)
    assert result["status"] == "uncertain"
    assert result["evidence"]["independent_source_text_assurance"]["sources"][0]["source_counterstatement_status"] == "counterstatement_observed"


@pytest.mark.parametrize("extra", [
    "",
    "Other unrelated publication information.",
    "Python 3.12.0 was not released on October 7, 2024.",
    "Python 3.12.0 was released on January 1, 1900.",
    "Python 3.13.0 is a stable release.",
    "The phrase is controversial and might be taken out of context.",
    "Python 3.13.0 is a Python release.",
])
def test_no_recognized_counterstatement_preserves_bounded_alignment(extra):
    observed = SOURCE_RELEASE if not extra else SOURCE_RELEASE + "\n" + extra
    result = _state(observed=observed)
    assert result["status"] == "supported"
    audit = result["evidence"]["independent_source_text_assurance"]["sources"][0]
    assert audit["source_counterstatement_status"] == "no_bounded_counterstatement_observed"
    assert audit["assertion_context_status"] == "unique_standalone_unit"
    assert result["evidence"]["claim_alignment"]["status"] == "aligned"
    assert result["evidence"]["claim_alignment"]["semantic_support_verified"] is False


def test_trusted_source_assurance_remains_identical_for_legacy_strict_mode():
    observed = SOURCE_RELEASE + "\n" + NEGATED_RELEASE
    result = _state(observed=observed, claim_mode=False)
    assert result["status"] == "supported"
    row = result["evidence"]["independent_source_text_assurance"]["sources"][0]
    assert row["status"] == "exact_text_observed"
    assert "source_counterstatement_status" not in row
    assert "claim_alignment" not in result["evidence"]


def test_real_html_structural_lines_are_separately_considered():
    html = (
        "<html><body><h1>" + STABLE + "</h1>"
        "<p>" + NEGATED_STABLE + "</p></body></html>"
    )
    observed = _decode_observed_content(html.encode(), "text/html; charset=utf-8")
    assert "\n" in observed
    result = _state(STABLE, observed, "Python 3.13.0 is a stable release.")
    assert result["status"] == "uncertain"
    assert result["evidence"]["independent_source_text_assurance"]["sources"][0]["reason"] == "independent_source_explicit_counterstatement"


def test_real_fastapi_path_refuses_counterstatement_and_client_override(monkeypatch):
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([URL]))
    observed = SOURCE_RELEASE + "\n" + NEGATED_RELEASE
    monkeypatch.setattr(
        AllowlistedHttpsSourceReader, "__call__",
        lambda self, url: _reader(observed)(url),
    )
    payload = {
        "task": "Check the release date",
        "entity": "Python 3.13.0",
        "documents": [{"uri": URL, "content": SOURCE_RELEASE}],
        "require_independent_source_text_match": True,
        "require_claim_alignment": True,
        "claim_text": SOURCE_RELEASE,
        "freshness_max_age_seconds": 3600,
    }
    with TestClient(app) as client:
        response = client.post("/api/v1/reality-state/evidence", json=payload)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "uncertain"
        assert result["evidence"]["independent_source_text_assurance"]["sources"][0]["reason"] == "independent_source_explicit_counterstatement"
        payload["documents"][0]["source_counterstatement_status"] = "no_bounded_counterstatement_observed"
        assert client.post("/api/v1/reality-state/evidence", json=payload).status_code == 422


def test_no_extra_source_reader_call_and_no_body_leak():
    calls = []
    observed = SOURCE_RELEASE + "\n" + NEGATED_RELEASE
    def read(uri):
        calls.append(uri)
        return _reader(observed)(uri)
    deps = replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(read),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
    )
    result = build_reality_state_from_evidence(
        "Check statement",
        [{"uri": URL, "content": SOURCE_RELEASE}],
        entity="Python 3.13.0",
        freshness_max_age_seconds=3600,
        require_independent_source_text_match=True,
        require_claim_alignment=True,
        claim_text=SOURCE_RELEASE,
        dependencies=deps,
    )
    assert calls == [URL]
    assert NEGATED_RELEASE not in json.dumps(result)
    assert result["evidence"]["independent_source_text_assurance"]["sources"][0]["observer_content_sha256"] is None


def test_raw_caller_receipt_cannot_bypass_server_counterstatement_requirement():
    bundle = SubmittedEvidenceBundle.from_mappings([{"uri": URL, "content": SOURCE_RELEASE}])
    receipt = IndependentSourceTextAssurance(_reader(SOURCE_RELEASE)).check(
        bundle, require_unique_standalone_unit=True,
    )
    assert receipt["status"] == "exact_text_observed"
    forged = dict(receipt)
    forged["sources"] = [dict(receipt["sources"][0])]
    forged["sources"][0].pop("source_counterstatement_status")
    assert evaluate_claim_alignment(SOURCE_RELEASE, bundle, forged)["status"] == "insufficient"


@pytest.mark.parametrize("invalid_body", [None, "", "x" * (MAX_OBSERVED_SOURCE_CHARS + 1)])
def test_source_scanner_strict_input_bounds(invalid_body):
    if invalid_body is None or len(invalid_body) > MAX_OBSERVED_SOURCE_CHARS:
        with pytest.raises(ValueError):
            has_bounded_source_counterstatement(invalid_body, SOURCE_RELEASE)
    else:
        assert has_bounded_source_counterstatement(invalid_body, SOURCE_RELEASE) is False


def test_scanner_is_bound_to_tiny_structured_grammar_not_claimed_general_semantics():
    assert has_bounded_source_counterstatement(
        SOURCE_RELEASE + "\n" + NEGATED_RELEASE, SOURCE_RELEASE
    )
    assert not has_bounded_source_counterstatement(
        SOURCE_RELEASE + "\nThis may be misleading or inaccurate.", SOURCE_RELEASE
    )
    assert not has_bounded_source_counterstatement(
        SOURCE_RELEASE + "\nThe evidence requires further investigation.", SOURCE_RELEASE
    )


def test_two_publishers_one_source_counterstatement_prevents_all_source_support():
    second_uri = "https://www.iana.org/domains/reserved"
    documents = [
        {"uri": URL, "content": SOURCE_RELEASE},
        {"uri": second_uri, "content": SOURCE_RELEASE},
    ]
    bodies = {
        URL: SOURCE_RELEASE,
        second_uri: SOURCE_RELEASE + "\n" + NEGATED_RELEASE,
    }
    def read(uri):
        body = bodies[uri]
        return {
            "uri": uri, "content": body,
            "capture_sha256": sha256(body.encode()).hexdigest(),
            "capture_observed_at": NOW.isoformat().replace("+00:00", "Z"),
            "observed_quote_unit_sha256": [],
        }
    deps = replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(read),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
    )
    state = build_reality_state_from_evidence(
        "Check corroboration",
        documents,
        entity="Python 3.13.0",
        freshness_max_age_seconds=3600,
        require_independent_source_text_match=True,
        require_claim_alignment=True,
        claim_text=SOURCE_RELEASE,
        dependencies=deps,
    )
    assert state["status"] == "uncertain"
    source_audits = state["evidence"]["independent_source_text_assurance"]["sources"]
    assert source_audits[0]["status"] == "exact_text_observed"
    assert source_audits[0]["source_counterstatement_status"] == "no_bounded_counterstatement_observed"
    assert source_audits[1]["status"] == "unverified"
    assert source_audits[1]["source_counterstatement_status"] == "counterstatement_observed"
    assert state["evidence"]["claim_alignment"]["status"] == "insufficient"
