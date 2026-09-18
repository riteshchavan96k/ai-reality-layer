import pytest

from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest


def test_provider_request_preserves_freshness_requirement():
    request = RetrievalProviderRequest(
        query="current information",
        source_type="live_web",
        temporal_scope="current",
        required=True,
        freshness_max_age_seconds=300,
    )

    assert request.to_dict()["freshness_max_age_seconds"] == 300

    restored = RetrievalProviderRequest.from_mapping(request.to_dict())
    assert restored == request


def test_provider_request_rejects_invalid_freshness_requirement():
    with pytest.raises(ValueError):
        RetrievalProviderRequest(
            query="x",
            source_type="live_web",
            freshness_max_age_seconds=0,
        )

    with pytest.raises(ValueError):
        RetrievalProviderRequest(
            query="x",
            source_type="live_web",
            freshness_max_age_seconds=-1,
        )

    with pytest.raises(ValueError):
        RetrievalProviderRequest(
            query="x",
            source_type="live_web",
            freshness_max_age_seconds=True,
        )


def test_configured_external_provider_dependency_is_constructible(monkeypatch):
    monkeypatch.setenv(
        "ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE",
        "https://example.test/search?q={query}",
    )

    dependencies = OrchestrationDependencies.default()

    assert dependencies.retrieval_provider_registry.get("live_web").provider_name == "http_retrieval"


def test_provider_request_omits_unspecified_freshness_for_backward_compatibility():
    request = RetrievalProviderRequest(query="x", source_type="live_web")

    assert "freshness_max_age_seconds" not in request.to_dict()
