from backend.app.reality.http_retrieval_provider import HttpRetrievalProvider
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest


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
    return RetrievalProviderRequest(query="test", source_type="live_web", temporal_scope="current")


def test_failed_external_status_is_preserved():
    result = provider_for({"status": "failed", "reason": "upstream_failed"}).retrieve(request())
    assert result.status == "failed"
    assert result.reason == "upstream_failed"


def test_blocked_external_status_is_preserved():
    result = provider_for({"status": "blocked", "reason": "upstream_blocked"}).retrieve(request())
    assert result.status == "blocked"
    assert result.reason == "upstream_blocked"


def test_unsupported_external_status_fails_closed():
    result = provider_for({"status": "success"}).retrieve(request())
    assert result.status == "failed"
    assert result.reason == "invalid_provider_status"


def test_invalid_external_reason_fails_closed():
    result = provider_for({"status": "failed", "reason": 123}).retrieve(request())
    assert result.status == "failed"
    assert result.reason == "invalid_provider_reason"


def test_completed_external_status_remains_completed():
    result = provider_for({"status": "completed", "content": "hello"}).retrieve(request())
    assert result.status == "completed"
    assert result.content == "hello"
