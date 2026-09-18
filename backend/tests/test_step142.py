import pytest

from backend.app.reality.http_retrieval_provider import HttpRetrievalProvider
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse


def provider_for(payload):
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size): return __import__("json").dumps(payload).encode()

    return HttpRetrievalProvider(
        "https://example.test/search?q={query}",
        opener=lambda request, timeout: Response(),
    )


def request():
    return RetrievalProviderRequest(
        query="test",
        source_type="live_web",
        temporal_scope="current",
    )


def test_non_completed_response_rejects_sources():
    with pytest.raises(ValueError, match="non-completed responses must not contain sources"):
        RetrievalProviderResponse(
            status="failed",
            sources=({"uri": "https://example.test/source"},),
        )


def test_non_completed_response_rejects_content():
    with pytest.raises(ValueError, match="non-completed responses must not contain content"):
        RetrievalProviderResponse(status="blocked", content="unexpected")


def test_external_failed_payload_with_content_fails_closed():
    result = provider_for(
        {"status": "failed", "reason": "upstream_failed", "content": "unexpected"}
    ).retrieve(request())
    assert result.status == "failed"
    assert result.reason == "invalid_non_completed_payload"


def test_external_blocked_payload_with_sources_fails_closed():
    result = provider_for(
        {
            "status": "blocked",
            "reason": "upstream_blocked",
            "sources": [{"uri": "https://example.test/source"}],
        }
    ).retrieve(request())
    assert result.status == "failed"
    assert result.reason == "invalid_non_completed_payload"


def test_external_non_completed_payload_without_data_preserves_status():
    result = provider_for(
        {"status": "provider_unavailable", "reason": "upstream_unavailable"}
    ).retrieve(request())
    assert result.status == "provider_unavailable"
    assert result.content is None
    assert result.sources == ()
    assert result.reason == "upstream_unavailable"


def test_completed_response_can_contain_content_and_sources():
    result = RetrievalProviderResponse(
        status="completed",
        sources=({"uri": "https://example.test/source"},),
        content="valid",
    )
    assert result.status == "completed"
    assert result.content == "valid"
    assert len(result.sources) == 1
