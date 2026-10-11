"""Step 228: source context cannot be silently dropped before claim alignment.

Every reader here is an *injected test transport*, not real publisher HTTPS.
The unchanged hosted original-source canaries separately test the live path.
"""

from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json

from fastapi.testclient import TestClient
import pytest

from backend.app.main import app
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.claim_assertion_alignment import evaluate_claim_alignment
from backend.app.reality.independent_source_text_assurance import (
    IndependentSourceTextAssurance, _unique_standalone_source_unit,
)
from backend.app.reality.allowlisted_https_source_reader import (
    AllowlistedHttpsSourceReader, _decode_observed_content,
)
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle

URI = "https://www.python.org/downloads/release/python-3130/"
CLAIM = "Python 3.13.0 was released on October 7, 2024."
ORIGINAL = "This is the stable release of Python 3.13.0"
SEMANTIC_CLAIM = "Python 3.13.0 is a stable release."
NOW = datetime.now(timezone.utc)


def provider(body):
    def read(uri):
        return {
            "uri": uri,
            "content": body,
            "capture_sha256": sha256(body.encode("utf-8")).hexdigest(),
            "capture_observed_at": NOW.isoformat().replace("+00:00", "Z"),
        }
    return read


def state(excerpt, observed, claim=CLAIM, *, alignment=True):
    dependencies = replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(provider(observed)),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
    )
    return build_reality_state_from_evidence(
        "Evaluate the explicit factual assertion",
        [{"uri": URI, "content": excerpt}],
        entity="Python 3.13.0",
        freshness_max_age_seconds=3600,
        require_independent_source_text_match=True,
        require_claim_alignment=alignment,
        claim_text=claim if alignment else None,
        dependencies=dependencies,
    )


@pytest.mark.parametrize("observed", [
    "It is false that " + CLAIM,
    "The claim that " + CLAIM + " is false.",
    "Unverified reports state: " + CLAIM,
    "The publisher disputes " + CLAIM,
    "The following false rumor appears: " + CLAIM,
    'A quotation reads "' + CLAIM + '"',
    CLAIM + " This paragraph later denies the assertion.",
    "Unrelated context before " + CLAIM + " and after.",
    CLAIM + "\nIt is false that " + CLAIM,
    CLAIM + "\n" + CLAIM,
    "Notice that " + CLAIM + "\nA different paragraph.",
])
def test_cherry_picked_embedded_excerpt_refused_by_real_assurance(observed):
    assert CLAIM in observed
    result = state(CLAIM, observed)
    assert result["status"] == "uncertain"
    assert result["evidence"]["claim_alignment"]["status"] == "insufficient"
    assurance = result["evidence"]["independent_source_text_assurance"]
    assert assurance["status"] == "unverified"
    assert assurance["sources"][0]["reason"] == "excerpt_not_unique_standalone_source_unit"
    assert assurance["sources"][0]["assertion_context_status"] == "unverified"
    assert assurance["sources"][0]["capture_sha256"] is None


def test_existing_text_presence_contract_preserved_for_non_claim_callers():
    body = "It is false that " + CLAIM
    strict = state(CLAIM, body, alignment=False)
    assert strict["evidence"]["independent_source_text_assurance"]["status"] == "exact_text_observed"
    assert "assertion_context_status" not in strict["evidence"]["independent_source_text_assurance"]["sources"][0]
    assert "claim_alignment" not in strict["evidence"]


@pytest.mark.parametrize("observed", [
    CLAIM,
    "Other structural block.\n" + CLAIM,
    CLAIM + "\nOther structural block.",
    "Other block.\n  " + CLAIM + "  \nAnother block.",
])
def test_single_complete_unit_preserves_scoped_support(observed):
    s = state(CLAIM, observed)
    assert s["status"] == "supported"
    audit = s["evidence"]["independent_source_text_assurance"]["sources"][0]
    assert audit["assertion_context_status"] == "unique_standalone_unit"
    assert len(audit["capture_sha256"]) == 64
    assert s["evidence"]["claim_alignment"]["status"] == "aligned"
    assert s["evidence"]["claim_alignment"]["semantic_support_verified"] is False


def test_html_heading_unit_and_unrelated_blocks_preserve_real_publisher_control():
    rendered = _decode_observed_content(
        ("<html><body><h1>" + ORIGINAL + "</h1><p>Other details.</p></body></html>").encode(),
        "text/html; charset=utf-8",
    )
    assert ORIGINAL in rendered
    s = state(ORIGINAL, rendered, claim=SEMANTIC_CLAIM)
    assert s["status"] == "supported"
    assert s["evidence"]["claim_alignment"]["status"] == "aligned"


def test_html_longer_visible_paragraph_cannot_embed_a_complete_quote():
    html = "<html><body><p>The claim that " + CLAIM + " is false.</p></body></html>"
    rendered = _decode_observed_content(html.encode(), "text/html; charset=utf-8")
    assert state(CLAIM, rendered)["status"] == "uncertain"


def test_capture_metadata_is_backend_owned_and_not_accepted_from_request(monkeypatch):
    monkeypatch.setenv("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", json.dumps([URI]))
    body = "It is false that " + CLAIM
    monkeypatch.setattr(AllowlistedHttpsSourceReader, "__call__", lambda self, uri: provider(body)(uri))
    with TestClient(app) as client:
        payload = {
            "task": "Verify the actual claim, not the isolated text",
            "entity": "Python 3.13.0",
            "documents": [{"uri": URI, "content": CLAIM}],
            "freshness_max_age_seconds": 3600,
            "require_independent_source_text_match": True,
            "require_claim_alignment": True,
            "claim_text": CLAIM,
        }
        response = client.post("/api/v1/reality-state/evidence", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "uncertain"
        assert response.json()["evidence"]["independent_source_text_assurance"]["sources"][0]["reason"] == "excerpt_not_unique_standalone_source_unit"
        payload["documents"][0]["assertion_context_status"] = "unique_standalone_unit"
        injected = client.post("/api/v1/reality-state/evidence", json=payload)
        assert injected.status_code == 422


def test_source_assurance_enforces_true_boolean_mode():
    bundle = SubmittedEvidenceBundle.from_mappings([{"uri": URI, "content": CLAIM}])
    with pytest.raises(ValueError, match="must be boolean"):
        IndependentSourceTextAssurance(provider(CLAIM)).check(
            bundle, require_unique_standalone_unit="yes"
        )


@pytest.mark.parametrize("body,expected", [
    (CLAIM, True),
    (CLAIM + "\nOther text.", True),
    (CLAIM + " More text.", False),
    ("Bad context " + CLAIM, False),
    (CLAIM + "\n" + CLAIM, False),
    ("One " + CLAIM + "\n" + CLAIM, False),
    (CLAIM + "\rOther text.", False),
])
def test_unit_detector_is_exact_conservative_and_duplicate_sensitive(body, expected):
    assert _unique_standalone_source_unit(body, CLAIM) is expected


def test_direct_claim_alignment_rejects_handcrafted_context_free_status():
    bundle = SubmittedEvidenceBundle.from_mappings([{"uri": URI, "content": CLAIM}])
    receipt = IndependentSourceTextAssurance(provider(CLAIM)).check(bundle)
    assert receipt["status"] == "exact_text_observed"
    assert evaluate_claim_alignment(CLAIM, bundle, receipt)["status"] == "insufficient"
