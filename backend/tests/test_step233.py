"""Step 233: exact bounded abstention/explanation policy regression tests.

Mock reader data proves classification wiring, NOT publisher observation.
The separate Step 233 hosted live workflow verifies original TLS retrieval.
"""
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256

import pytest

from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.independent_source_text_assurance import IndependentSourceTextAssurance


URL = "https://www.python.org/downloads/release/python-3130/"
URL2 = "https://www.iana.org/domains/reserved"
CLAIM = "Python 3.13.0 is a stable release."
EXCERPT = "This is the stable release of Python 3.13.0"
DATE_CLAIM = "Python 3.13.0 was released on October 7, 2024."
DATE_LABEL = "Release date: Oct. 7, 2024"
REASONS = frozenset({
    "source_quoted_unit",
    "source_counterstatement_observed",
    "independent_source_unverified",
    "source_assertion_context_unverified",
    "source_capture_receipt_invalid",
    "claim_grammar_unsupported",
    "source_grammar_unsupported",
    "bounded_assertion_aligned",
    "bounded_assertion_contradicted",
    "atomic_relationship_undetermined",
})


def get_result(claim=CLAIM, excerpt=EXCERPT, *, actual=None, quoted=False, capture=True,
               two_sources=False):
    def read(uri):
        body = excerpt if actual is None else actual
        r = {
            "uri": uri,
            "content": body,
            "observed_quote_unit_sha256": (
                [sha256(excerpt.encode()).hexdigest()] if quoted else []
            ),
        }
        if capture:
            r.update({
                "capture_sha256": sha256(body.encode()).hexdigest(),
                "capture_observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            })
        return r
    deps = replace(
        OrchestrationDependencies.default(),
        independent_source_text_assurance=IndependentSourceTextAssurance(read),
    )
    documents = [{"uri": URL, "content": excerpt}]
    if two_sources:
        documents.append({"uri": URL2, "content": excerpt})
    return build_reality_state_from_evidence(
        "Verify bounded claim", documents, dependencies=deps,
        entity=None,
        freshness_max_age_seconds=3600,
        require_independent_source_text_match=True,
        require_claim_alignment=True,
        claim_text=claim,
    )["evidence"]["claim_alignment"]


@pytest.mark.parametrize("claim,excerpt,actual,quoted,capture,expected_alignment,reason", [
    (CLAIM, EXCERPT, None, False, True, "aligned", "bounded_assertion_aligned"),
    ("Python 3.13.0 is not a stable release.", EXCERPT, None, False, True, "contradicted", "bounded_assertion_contradicted"),
    (DATE_CLAIM, DATE_LABEL, None, False, True, "insufficient", "source_grammar_unsupported"),
    ("Python 3.12.0 is a stable release.", EXCERPT, None, False, True, "insufficient", "atomic_relationship_undetermined"),
    ("Python 3.13.0 might be a stable release.", EXCERPT, None, False, True, "insufficient", "claim_grammar_unsupported"),
    (CLAIM, EXCERPT, "Unrelated observed text.", False, True, "insufficient", "independent_source_unverified"),
    (CLAIM, EXCERPT, None, True, True, "insufficient", "source_quoted_unit"),
    (CLAIM, EXCERPT, None, False, False, "insufficient", "source_capture_receipt_invalid"),
])
def test_bounded_source_decision_reasons(
    claim, excerpt, actual, quoted, capture, expected_alignment, reason
):
    a = get_result(claim, excerpt, actual=actual, quoted=quoted, capture=capture)
    assert a["status"] == expected_alignment
    assert a["decision_reasons"] == [{"source_ref": URL, "code": reason}]
    assert len(a["decision_reasons"]) == len(a["source_decisions"]) == 1
    assert a["source_decisions"][0]["relationship"] == expected_alignment
    assert a["semantic_support_verified"] is False
    assert a["factual_truth_verified"] is False
    assert reason in REASONS


def test_multiple_sources_preserve_order_source_identity_and_no_raw_content():
    a = get_result(two_sources=True)
    assert a["status"] == "aligned"
    assert a["decision_reasons"] == [
        {"source_ref": URL, "code": "bounded_assertion_aligned"},
        {"source_ref": URL2, "code": "bounded_assertion_aligned"},
    ]
    assert EXCERPT not in str(a["decision_reasons"])
    assert CLAIM not in str(a["decision_reasons"])
    assert all(set(r) == {"source_ref", "code"} for r in a["decision_reasons"])


def test_reason_codes_do_not_reflect_untrusted_reader_error():
    attacker = "private credentials 1234 do not reveal"
    a = get_result(actual=attacker)
    assert a["decision_reasons"][0]["code"] == "independent_source_unverified"
    assert attacker not in str(a["decision_reasons"])
