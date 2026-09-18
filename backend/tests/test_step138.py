from backend.app.reality.http_retrieval_provider import HttpRetrievalProvider


def provider():
    return HttpRetrievalProvider("https://example.test/search?q={query}")


def test_rejects_source_with_invalid_uri():
    result = provider()._normalize_payload(
        {"content": "fact", "sources": [{"uri": "javascript:bad", "title": "bad"}]},
        "https://example.test/search?q=fact",
    )
    assert result.status == "failed"
    assert result.reason == "invalid_source_uri"


def test_rejects_source_with_invalid_title_type():
    result = provider()._normalize_payload(
        {"content": "fact", "sources": [{"uri": "https://example.test/fact", "title": 123}]},
        "https://example.test/search?q=fact",
    )
    assert result.status == "failed"
    assert result.reason == "invalid_source_title"


def test_rejects_source_without_provenance():
    result = provider()._normalize_payload(
        {"content": "fact", "sources": [{"snippet": "fact"}]},
        "https://example.test/search?q=fact",
    )
    assert result.status == "failed"
    assert result.reason == "source_missing_provenance"


def test_accepts_http_and_https_source_uris():
    result = provider()._normalize_payload(
        {
            "content": "facts",
            "sources": [
                {"uri": "https://example.test/a", "title": "A"},
                {"uri": "http://example.test/b", "title": "B"},
            ],
        },
        "https://example.test/search?q=facts",
    )
    assert result.status == "completed"
    assert len(result.sources) == 2
