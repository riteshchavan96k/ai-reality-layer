"""Step 184 — Bounded retrieved evidence and claim amplification safety."""

import json

import pytest

from backend.app.orchestrator.orchestrator import build_reality_state
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer
from backend.app.reality.http_retrieval_provider import HttpRetrievalProvider
from backend.app.reality.retrieval_input_bounds import (
    MAX_RETRIEVED_CLAIMS,
    MAX_RETRIEVED_SOURCES,
    MAX_RETRIEVED_SOURCE_CONTENT_CHARS,
    MAX_RETRIEVED_URI_CHARS,
    MAX_RETRIEVED_TITLE_CHARS,
    validate_retrieved_evidence_bounds,
)
from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse
from backend.app.reality.submitted_evidence import (
    MAX_SUBMITTED_CONTENT_CHARS,
    MAX_SUBMITTED_DOCUMENTS,
    MAX_SUBMITTED_TITLE_CHARS,
    MAX_SUBMITTED_URI_CHARS,
)


TEMPLATE = "https://gateway.example.test/search?q={query}"
URI_A = "https://example.test/a"
URI_B = "https://example.test/b"


def _source(uri=URI_A, content="A fact.", **kwargs):
    return {"uri": uri, "content": content, **kwargs}


def _http(payload):
    return HttpRetrievalProvider(TEMPLATE)._normalize_payload(
        payload, TEMPLATE.replace("{query}", "facts"),
    )


def _request():
    return RetrievalProviderRequest(
        query="Company X latest status",
        source_type="live_web",
        temporal_scope="current",
    )


def _evidence(sources, content=None):
    return {
        "status": "completed",
        "sources": sources,
        "content": content,
    }


def test_retrieval_limits_match_existing_mvp_evidence_limits():
    assert MAX_RETRIEVED_SOURCES == MAX_SUBMITTED_DOCUMENTS
    assert MAX_RETRIEVED_SOURCE_CONTENT_CHARS == MAX_SUBMITTED_CONTENT_CHARS
    assert MAX_RETRIEVED_URI_CHARS == MAX_SUBMITTED_URI_CHARS
    assert MAX_RETRIEVED_TITLE_CHARS == MAX_SUBMITTED_TITLE_CHARS
    assert MAX_RETRIEVED_CLAIMS > 0


def test_evidence_limits_accept_exact_legacy_single_document_boundary():
    assert validate_retrieved_evidence_bounds(
        [{"uri": URI_A, "title": "T" * MAX_RETRIEVED_TITLE_CHARS}],
        "x" * MAX_RETRIEVED_SOURCE_CONTENT_CHARS,
    ) is None


def test_evidence_limits_accept_exact_source_uri_boundary():
    uri = "https://example.test/" + (
        "x" * (MAX_RETRIEVED_URI_CHARS - len("https://example.test/"))
    )
    assert len(uri) == MAX_RETRIEVED_URI_CHARS
    assert validate_retrieved_evidence_bounds([_source(uri=uri)], None) is None


def test_evidence_limits_accept_maximum_source_count_with_scoped_text():
    sources = [
        _source(uri=f"https://example.test/doc/{i}", content=f"Document {i}.")
        for i in range(MAX_RETRIEVED_SOURCES)
    ]
    assert validate_retrieved_evidence_bounds(sources, None) is None
    result = _http({"status": "completed", "sources": sources})
    assert result.status == "completed"
    assert len(result.sources) == MAX_RETRIEVED_SOURCES


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (
            {
                "sources": [
                    _source(uri=f"https://example.test/doc/{i}")
                    for i in range(MAX_RETRIEVED_SOURCES + 1)
                ]
            },
            "too_many_sources",
        ),
        (
            {"sources": [_source(uri=URI_A + "x" * MAX_RETRIEVED_URI_CHARS)]},
            "source_uri_too_long",
        ),
        (
            {"sources": [_source(title="T" * (MAX_RETRIEVED_TITLE_CHARS + 1))]},
            "source_title_too_long",
        ),
        (
            {"sources": [_source(content="x" * (
                MAX_RETRIEVED_SOURCE_CONTENT_CHARS + 1
            ))]},
            "source_content_too_large",
        ),
        (
            {
                "content": "x" * (MAX_RETRIEVED_SOURCE_CONTENT_CHARS + 1),
                "sources": [{"uri": URI_A}],
            },
            "retrieved_content_too_large",
        ),
        (
            {"content": "x" * (MAX_RETRIEVED_SOURCE_CONTENT_CHARS + 1)},
            "retrieved_content_too_large",
        ),
        (
            {
                "sources": [
                    _source(extra={"untrusted": ["x" * 100] * 30}),
                ]
            },
            "unexpected_source_metadata",
        ),
        (
            {"sources": [
                _source(observed_at="x" * 65),
            ]},
            "invalid_source_observed_at",
        ),
    ],
)
def test_http_rejects_unbounded_sources_without_any_partial_output(payload, reason):
    result = _http(payload)
    assert result.status == "failed"
    assert result.reason == reason
    assert result.content is None
    assert result.sources == ()


def test_http_preserves_old_non_completed_failure_reason():
    result = _http({"status": "failed", "reason": "upstream_failed"})
    assert result.status == "failed"
    assert result.reason == "upstream_failed"


def test_legacy_provider_neutral_scalar_source_fields_remain_compatible():
    # Old typed/legacy contracts used id and url fields. Keep them bounded
    # but never elevate those fields to canonical claim provenance.
    response = RetrievalProviderResponse(
        status="completed",
        sources=({
            "uri": URI_A,
            "id": "doc-1",
            "url": "https://old.example.test/source",
            "title": "Original",
        },),
        content="Safe legacy evidence.",
    )
    assert response.status == "completed"
    normalized = RetrievalEvidenceNormalizer().normalize_result(
        _evidence(list(response.sources), response.content)
    )
    assert normalized.status == "completed"
    assert normalized.sources == [{"uri": URI_A, "title": "Original"}]


def test_many_or_oversized_legacy_scalar_fields_are_rejected():
    assert validate_retrieved_evidence_bounds(
        [{"uri": URI_A, **{f"legacy{i}": "ok" for i in range(5)}}],
        "A fact.",
    ) == "unexpected_source_metadata"
    assert validate_retrieved_evidence_bounds(
        [{"uri": URI_A, "url": "x" * 501}],
        "A fact.",
    ) == "unexpected_source_metadata"


def test_provider_neutral_legacy_response_rejects_oversized_sources():
    oversized = [
        _source(uri=f"https://example.test/doc/{i}")
        for i in range(MAX_RETRIEVED_SOURCES + 1)
    ]
    with pytest.raises(ValueError, match="too_many_sources"):
        RetrievalProviderResponse.from_mapping({
            "status": "completed", "sources": oversized,
        })


def test_provider_neutral_typed_response_rejects_unbounded_metadata():
    with pytest.raises(ValueError, match="unexpected_source_metadata"):
        RetrievalProviderResponse(
            status="completed",
            sources=({"uri": URI_A, "metadata": {"huge": "x" * 50000}},),
            content="ok",
        )


def test_provider_executor_fails_closed_for_oversized_legacy_mapping():
    class OversizedProvider:
        provider_name = "oversized_demo"

        def retrieve(self, request):
            return {
                "status": "completed",
                "sources": [
                    _source(uri=f"https://example.test/doc/{i}")
                    for i in range(MAX_RETRIEVED_SOURCES + 1)
                ],
                "content": "ok",
            }

    result = RetrievalProviderExecutor().execute(OversizedProvider(), _request())
    assert result["status"] == "failed"
    assert result["reason"] == "retrieval_provider_failed"
    assert result["sources"] == []


@pytest.mark.parametrize(
    "sources, content",
    [
        (
            [_source(uri=f"https://example.test/doc/{i}")
             for i in range(MAX_RETRIEVED_SOURCES + 1)],
            None,
        ),
        ([_source(content="x" * (
            MAX_RETRIEVED_SOURCE_CONTENT_CHARS + 1
        ))], None),
        ([{"uri": URI_A}], "x" * (
            MAX_RETRIEVED_SOURCE_CONTENT_CHARS + 1
        )),
        ([_source(extra="nested" * 50_000)], None),
    ],
)
def test_evidence_normalizer_drops_invalid_provider_neutral_evidence(sources, content):
    normalized = RetrievalEvidenceNormalizer().normalize_result(
        _evidence(sources, content)
    )
    assert normalized.status == "invalid_evidence"
    assert normalized.sources == []
    assert normalized.content is None
    assert normalized.has_content is False
    assert normalized.source_count == 0


def test_evidence_normalizer_preserves_valid_182_183_fields():
    sources = [
        _source(uri=URI_A, title="Original", observed_at="2026-01-01T12:30:00Z"),
        _source(uri=URI_B, content="B fact."),
    ]
    result = RetrievalEvidenceNormalizer().normalize_result(
        _evidence(sources)
    )
    assert result.status == "completed"
    assert result.source_count == 2
    assert result.sources[0]["observed_at"] == "2026-01-01T12:30:00Z"
    assert result.sources[0]["content"] == "A fact."


def _many_claims(n):
    return " ".join(f"Claim {i}." for i in range(n))


def test_retrieved_claim_limit_inclusive_boundary():
    content = _many_claims(MAX_RETRIEVED_CLAIMS)
    assert len(content) < MAX_RETRIEVED_SOURCE_CONTENT_CHARS
    extracted = EvidenceClaimExtractor().extract_result(
        _evidence([_source(content=content)], content)
    )
    assert extracted.status == "usable"
    assert len(extracted.claims) == MAX_RETRIEVED_CLAIMS


def test_retrieved_claim_limit_fails_closed_before_linking():
    content = _many_claims(MAX_RETRIEVED_CLAIMS + 1)
    assert len(content) < MAX_RETRIEVED_SOURCE_CONTENT_CHARS
    extracted = EvidenceClaimExtractor().extract_result(
        _evidence([_source(content=content)], content)
    )
    assert extracted.status == "unavailable"
    assert extracted.reason == "retrieved_claim_limit_exceeded"
    assert extracted.claims == ()


def test_direct_submitted_evidence_extraction_behavior_not_changed():
    # Existing "usable" direct-evidence claim contract is intentionally not
    # part of Step 184 retrieval-specific claim budget changes.
    content = _many_claims(MAX_RETRIEVED_CLAIMS + 1)
    extracted = EvidenceClaimExtractor().extract_result(
        {
            "status": "usable",
            "sources": [{"uri": URI_A}],
            "content": content,
        }
    )
    assert extracted.status == "usable"
    assert len(extracted.claims) == MAX_RETRIEVED_CLAIMS + 1


def _fake_http(monkeypatch, payload):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            data = json.dumps(payload).encode("utf-8")
            assert len(data) <= limit
            return data

    monkeypatch.setenv("ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE", TEMPLATE)
    monkeypatch.setattr(
        "backend.app.reality.http_retrieval_provider.urlopen",
        lambda request, timeout: Response(),
    )


def test_complete_reality_state_rejects_over_source_limit(monkeypatch):
    _fake_http(monkeypatch, {
        "sources": [
            _source(uri=f"https://example.test/doc/{i}")
            for i in range(MAX_RETRIEVED_SOURCES + 1)
        ]
    })
    result = build_reality_state("What is the current status of Company X?")
    assert result["claims"]["claims"] == []
    assert result["claim_evidence_linking"]["links"] == []
    assert result["status"] != "supported"


def test_complete_reality_state_rejects_over_claim_limit(monkeypatch):
    content = _many_claims(MAX_RETRIEVED_CLAIMS + 1)
    _fake_http(monkeypatch, {"sources": [_source(content=content)]})
    result = build_reality_state("What is the current status of Company X?")
    assert result["claims"]["status"] == "unavailable"
    assert result["claims"]["reason"] == "retrieved_claim_limit_exceeded"
    assert result["claim_evidence_linking"]["links"] == []
    assert result["status"] != "supported"


def test_complete_reality_state_keeps_valid_single_source(monkeypatch):
    _fake_http(monkeypatch, {"sources": [_source(content="Source claim.")]})
    result = build_reality_state("What is the current status of Company X?")
    assert result["claims"]["status"] == "usable"
    assert result["claims"]["claims"][0]["source_refs"] == [URI_A]
    assert result["freshness"]["unknown_count"] == 1
    assert result["status"] == "uncertain"
