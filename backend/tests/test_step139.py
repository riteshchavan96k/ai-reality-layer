from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.retrieval_provider_capabilities import RetrievalProviderCapabilities
from backend.app.reality.retrieval_provider_descriptor import RetrievalProviderDescriptor


class FakeProvider:
    provider_name = "fake"


def test_configured_external_provider_has_explicit_capabilities(monkeypatch):
    monkeypatch.setenv(
        "ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE",
        "https://example.test/search?q={query}",
    )
    dependencies = OrchestrationDependencies.default()

    live_descriptor = dependencies.retrieval_provider_registry.get_descriptor("live_web")
    external_descriptor = dependencies.retrieval_provider_registry.get_descriptor(
        "web_or_official_source"
    )

    assert isinstance(live_descriptor, RetrievalProviderDescriptor)
    assert isinstance(external_descriptor, RetrievalProviderDescriptor)
    assert live_descriptor.name == "http_retrieval"
    assert external_descriptor.name == "http_retrieval"
    assert live_descriptor.capabilities == external_descriptor.capabilities


def test_external_provider_capabilities_cover_current_and_unspecified_scopes():
    capabilities = RetrievalProviderCapabilities(
        source_types=("live_web", "web_or_official_source"),
        temporal_scopes=("current", "unspecified"),
    )

    assert "live_web" in capabilities.source_types
    assert "web_or_official_source" in capabilities.source_types
    assert "current" in capabilities.temporal_scopes
    assert "unspecified" in capabilities.temporal_scopes


def test_unconfigured_default_does_not_gain_external_capability_metadata(monkeypatch):
    monkeypatch.delenv("ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE", raising=False)
    dependencies = OrchestrationDependencies.default()

    assert dependencies.retrieval_provider_registry.get_descriptor("live_web") is None
    assert (
        dependencies.retrieval_provider_registry.get_descriptor("web_or_official_source")
        is None
    )
