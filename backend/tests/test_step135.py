import json
import pytest

from backend.app.reality.http_retrieval_provider import HttpRetrievalProvider
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit: int):
        return self.payload


def make_request():
    return RetrievalProviderRequest(query="latest test", source_type="live_web")


def test_http_provider_requires_explicit_https_query_template():
    with pytest.raises(ValueError):
        HttpRetrievalProvider("http://example.test?q={query}")
    with pytest.raises(ValueError):
        HttpRetrievalProvider("https://example.test/search")


def test_http_provider_url_encodes_query_and_normalizes_json():
    captured = {}

    def opener(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return FakeResponse(json.dumps({"content": "Observed fact", "sources": [{"uri": "https://source.test/a"}]}).encode())

    provider = HttpRetrievalProvider("https://example.test/search?q={query}", opener=opener)
    result = provider.retrieve(make_request())

    assert result.status == "completed"
    assert result.provider == "http_retrieval"
    assert result.content == "Observed fact"
    assert result.sources[0]["uri"] == "https://source.test/a"
    assert "latest%20test" in captured["url"]
    assert captured["timeout"] == 10.0


def test_http_provider_adds_request_source_when_content_has_no_sources():
    provider = HttpRetrievalProvider(
        "https://example.test/search?q={query}",
        opener=lambda request, timeout: FakeResponse(b'{"content":"fact"}'),
    )
    result = provider.retrieve(make_request())
    assert result.status == "completed"
    assert result.sources[0]["uri"].startswith("https://example.test/search?q=")


def test_http_provider_fails_closed_on_invalid_payload():
    provider = HttpRetrievalProvider(
        "https://example.test/search?q={query}",
        opener=lambda request, timeout: FakeResponse(b"not-json"),
    )
    result = provider.retrieve(make_request())
    assert result.status == "failed"
    assert result.reason == "http_retrieval_failed"


def test_http_provider_enforces_response_limit():
    provider = HttpRetrievalProvider(
        "https://example.test/search?q={query}",
        max_response_bytes=4,
        opener=lambda request, timeout: FakeResponse(b"12345"),
    )
    result = provider.retrieve(make_request())
    assert result.status == "failed"
    assert result.reason == "response_too_large"


def test_http_provider_rejects_wrong_request_type():
    provider = HttpRetrievalProvider("https://example.test/search?q={query}")
    with pytest.raises(ValueError):
        provider.retrieve({"query": "x"})


def test_default_dependencies_keep_external_provider_opt_in(monkeypatch):
    monkeypatch.delenv("ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE", raising=False)
    dependencies = OrchestrationDependencies.default()
    assert dependencies.retrieval_provider_registry.get("live_web").__class__.__name__ == "UnconfiguredRetrievalProvider"


def test_default_dependencies_register_configured_http_provider(monkeypatch):
    monkeypatch.setenv("ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE", "https://example.test/search?q={query}")
    dependencies = OrchestrationDependencies.default()
    provider = dependencies.retrieval_provider_registry.get("live_web")
    assert isinstance(provider, HttpRetrievalProvider)
