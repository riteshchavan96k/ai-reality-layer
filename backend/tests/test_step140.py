from backend.app.reality.retrieval_engine import RealityRetrievalEngine
from backend.app.reality.retrieval_provider_capabilities import RetrievalProviderCapabilities
from backend.app.reality.retrieval_provider_descriptor import RetrievalProviderDescriptor
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry

class RecordingProvider:
    provider_name = "recording"
    def __init__(self): self.calls = 0
    def retrieve(self, request):
        self.calls += 1
        return {"status": "completed", "provider": self.provider_name, "sources": [{"uri": "https://example.test/source"}], "content": "retrieved"}

def build_engine(provider, temporal_scopes):
    registry = RetrievalProviderRegistry()
    registry.register_descriptor("live_web", RetrievalProviderDescriptor(
        name=provider.provider_name,
        capabilities=RetrievalProviderCapabilities(source_types=("live_web",), temporal_scopes=temporal_scopes),
        provider=provider,
    ))
    from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
    from backend.app.reality.retrieval_provider_selector import RegistryRetrievalProviderSelector
    return RealityRetrievalEngine(provider_executor=RetrievalProviderExecutor(), provider_selector=RegistryRetrievalProviderSelector(registry))

def test_capability_mismatch_blocks_provider_execution():
    provider = RecordingProvider()
    result = build_engine(provider, ("current",)).retrieve({"status":"ready","request":{"query":"external evidence","source_type":"live_web","temporal_scope":"historical","required":True}})
    assert result["status"] == "blocked"
    assert result["retrieval_executed"] is False
    assert result["reason"] == "retrieval_provider_capability_mismatch"
    assert provider.calls == 0

def test_declared_capability_allows_provider_execution():
    provider = RecordingProvider()
    result = build_engine(provider, ("current",)).retrieve({"status":"ready","request":{"query":"latest information","source_type":"live_web","temporal_scope":"current","required":True}})
    assert result["status"] == "completed"
    assert result["retrieval_executed"] is True
    assert provider.calls == 1