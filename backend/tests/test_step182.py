"""Step 182: source-scoped retrieval attribution and provenance integrity."""

import json

import pytest

from backend.app.orchestrator.orchestrator import build_reality_state
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer
from backend.app.reality.http_retrieval_provider import HttpRetrievalProvider


URI_A = "https://example.test/original-a"
URI_B = "https://example.test/original-b"
RETRIEVAL_URL = "https://retrieval.example.test/search?q=current"


def _sources():
    return [
        {
            "uri": URI_A,
            "title": "Original A",
            "content": "Unique A. Shared evidence.",
        },
        {
            "uri": URI_B,
            "title": "Original B",
            "content": "Unique B. Shared evidence.",
        },
    ]


def _http_provider():
    return HttpRetrievalProvider(
        "https://retrieval.example.test/search?q={query}"
    )


def _normalize(payload):
    return _http_provider()._normalize_payload(payload, RETRIEVAL_URL)


def _fake_http(monkeypatch, payload):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            result = json.dumps(payload).encode("utf-8")
            assert len(result) <= limit
            return result

    def open_request(request, timeout):
        assert request.full_url.startswith(
            "https://retrieval.example.test/search?q="
        )
        assert timeout == 10.0
        return Response()

    monkeypatch.setenv(
        "ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE",
        "https://retrieval.example.test/search?q={query}",
    )
    monkeypatch.setattr(
        "backend.app.reality.http_retrieval_provider.urlopen",
        open_request,
    )


def test_http_provider_accepts_source_scoped_content_without_combined_body():
    result = _normalize({"status": "completed", "sources": _sources()})

    assert result.status == "completed"
    assert result.content == (
        "Unique A. Shared evidence.\n\nUnique B. Shared evidence."
    )
    assert list(result.sources) == _sources()


def test_http_provider_preserves_consistent_explicit_combined_body():
    content = "Unique A. Shared evidence.\n\nUnique B. Shared evidence."
    result = _normalize({
        "status": "completed",
        "content": content,
        "sources": _sources(),
    })

    assert result.status == "completed"
    assert result.content == content


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (
            {
                "content": "Some content.",
                "sources": [
                    {"uri": URI_A, "content": "First source."},
                    {"uri": URI_B},
                ],
            },
            "incomplete_source_scoped_content",
        ),
        (
            {"sources": [{"uri": URI_A, "content": None}]},
            "invalid_source_scoped_content",
        ),
        (
            {"sources": [{"uri": URI_A, "content": "   "}]},
            "invalid_source_scoped_content",
        ),
        (
            {
                "content": "Different summary.",
                "sources": [{"uri": URI_A, "content": "Original content."}],
            },
            "inconsistent_source_scoped_content",
        ),
        (
            {"sources": [{"uri": URI_A}, {"uri": URI_A}]},
            "duplicate_source_uri",
        ),
        (
            {"sources": [{"uri": URI_A}, {"title": "No URI"}]},
            "source_uri_required",
        ),
    ],
)
def test_http_provider_rejects_invalid_or_misleading_lineage(payload, reason):
    result = _normalize(payload)
    assert result.status == "failed"
    assert result.reason == reason
    assert result.sources == ()
    assert result.content is None


def test_http_provider_does_not_fabricate_origin_from_gateway_url():
    result = _normalize({"status": "completed", "content": "Unattributed."})
    assert result.status == "completed"
    assert result.sources == ()
    assert result.content == "Unattributed."
    assert RETRIEVAL_URL not in str(result.sources)


def test_evidence_normalizer_retains_scoped_contents_and_constructs_body():
    evidence = RetrievalEvidenceNormalizer().normalize_result(
        {
            "status": "completed",
            "content": None,
            "sources": _sources(),
        }
    )
    assert evidence.status == "completed"
    assert evidence.sources == _sources()
    assert evidence.source_count == 2
    assert evidence.has_content is True
    assert evidence.content == (
        "Unique A. Shared evidence.\n\nUnique B. Shared evidence."
    )


@pytest.mark.parametrize(
    "sources, content",
    [
        ([{"uri": URI_A, "content": "A."}, {"uri": URI_B}], "A."),
        ([{"uri": URI_A, "content": ""}], None),
        ([{"uri": URI_A, "content": "A."}], "Disagrees."),
        ([{"uri": URI_A}, {"uri": URI_A}], "Legacy."),
        ([{"title": "Title without original URI"}], "Text."),
    ],
)
def test_provider_neutral_evidence_normalizer_fails_closed(sources, content):
    result = RetrievalEvidenceNormalizer().normalize_result(
        {"status": "completed", "sources": sources, "content": content}
    )
    assert result.status == "invalid_evidence"
    assert result.has_content is False


def test_claim_extractor_preserves_actual_source_lineage_and_merges_duplicates():
    result = EvidenceClaimExtractor().extract_result(
        {
            "status": "completed",
            "content": "Unique A. Shared evidence.\n\nUnique B. Shared evidence.",
            "sources": _sources(),
        }
    )
    assert result.status == "usable"
    assert result.source_count == 2
    assert [claim.text for claim in result.claims] == [
        "Unique A.", "Shared evidence.", "Unique B.",
    ]
    assert [claim.source_refs for claim in result.claims] == [
        (URI_A,), (URI_A, URI_B), (URI_B,),
    ]


def test_legacy_combined_multi_source_claim_attribution_fails_closed():
    result = EvidenceClaimExtractor().extract_result(
        {
            "status": "completed",
            "content": "Statement without per-source origin.",
            "sources": [{"uri": URI_A}, {"uri": URI_B}],
        }
    )
    assert result.status == "unavailable"
    assert result.reason == "ambiguous_source_attribution"
    assert result.claims == ()
    assert result.source_count == 2


def test_unattributed_text_never_turns_into_claims():
    result = EvidenceClaimExtractor().extract_result(
        {"status": "completed", "content": "Unknown publisher.", "sources": []}
    )
    assert result.status == "unavailable"
    assert result.reason == "missing_source_attribution"
    assert result.claims == ()


def test_legacy_single_source_claim_extraction_is_unchanged():
    result = EvidenceClaimExtractor().extract_result(
        {
            "status": "completed",
            "content": "One statement. Another statement.",
            "sources": [{"uri": URI_A, "title": "Original"}],
        }
    )
    assert result.status == "usable"
    assert [claim.source_refs for claim in result.claims] == [
        (URI_A,), (URI_A,),
    ]


def test_configured_http_retrieval_preserves_end_to_end_source_lineage(monkeypatch):
    _fake_http(monkeypatch, {"status": "completed", "sources": _sources()})
    state = build_reality_state("What is the current status of Company X?")

    assert state["status"] == "uncertain"  # Observation-age window undeclared.
    assert state["evidence"]["status"] == "completed"
    assert state["evidence"]["sources"] == _sources()
    assert state["claims"]["status"] == "usable"

    claims = {c["text"]: c for c in state["claims"]["claims"]}
    assert claims["Unique A."]["source_refs"] == [URI_A]
    assert claims["Unique B."]["source_refs"] == [URI_B]
    assert claims["Shared evidence."]["source_refs"] == [URI_A, URI_B]

    links = state["claim_evidence_linking"]["links"]
    assert len(links) == 4
    assert {(link["claim_text"], link["source_ref"]) for link in links} == {
        ("Unique A.", URI_A),
        ("Unique B.", URI_B),
        ("Shared evidence.", URI_A),
        ("Shared evidence.", URI_B),
    }
    assert {
        source["uri"] for source in state["source_provenance"]["sources"]
    } == {URI_A, URI_B}
    assert state["freshness"]["unknown_count"] == 2
    assert state["confidence_signals"]["status"] == "uncertain"


def test_configured_http_legacy_combined_multi_source_fails_conservatively(
    monkeypatch,
):
    _fake_http(
        monkeypatch,
        {
            "content": "No source-specific document.",
            "sources": [{"uri": URI_A}, {"uri": URI_B}],
        },
    )
    state = build_reality_state("What is the current status of Company X?")

    assert state["claims"]["status"] == "unavailable"
    assert state["claims"]["reason"] == "ambiguous_source_attribution"
    assert state["claims"]["claims"] == []
    assert state["claim_evidence_linking"]["links"] == []
    assert state["status"] != "supported"


def test_configured_http_without_source_does_not_claim_provenance(monkeypatch):
    _fake_http(monkeypatch, {"content": "No publisher."})
    state = build_reality_state("What is the current status of Company X?")

    assert state["claims"]["claims"] == []
    assert state["source_provenance"]["sources"] == []
    assert state["claim_evidence_linking"]["links"] == []
    assert state["status"] != "supported"


def test_scoped_sources_with_explicit_negation_preserve_conflict_lineage(
    monkeypatch,
):
    _fake_http(
        monkeypatch,
        {
            "sources": [
                {"uri": URI_A, "content": "Company X is operating."},
                {"uri": URI_B, "content": "not Company X is operating."},
            ]
        },
    )
    state = build_reality_state("What is the current status of Company X?")

    assert state["conflicts"]["conflict_count"] == 1
    conflict = state["conflicts"]["conflicts"][0]
    assert set(conflict["positive_source_refs"]) == {URI_A}
    assert set(conflict["negative_source_refs"]) == {URI_B}
    assert state["confidence_signals"]["status"] == "uncertain"
