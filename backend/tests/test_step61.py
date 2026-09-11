import unittest

from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.retrieval_engine import RealityRetrievalEngine
from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_selector import RegistryRetrievalProviderSelector


class ProviderA:
    name = "provider_a"

    def retrieve(self, request):
        return {"status": "completed", "provider": self.name, "sources": [], "content": "A"}


class ProviderB:
    name = "provider_b"

    def retrieve(self, request):
        return {"status": "completed", "provider": self.name, "sources": [], "content": "B"}


class Step61RetrievalProviderSelectionBoundaryTests(unittest.TestCase):
    def test_selector_chooses_provider_by_source_type(self):
        registry = RetrievalProviderRegistry(
            providers={"live_web": ProviderA(), "web_or_official_source": ProviderB()},
            default_provider=ProviderA(),
        )
        selector = RegistryRetrievalProviderSelector(registry)

        self.assertEqual(selector.select({"source_type": "live_web"}).status, "selected")
        self.assertIsInstance(selector.select({"source_type": "live_web"}).provider, ProviderA)
        self.assertEqual(
            selector.select({"source_type": "web_or_official_source"}).provider.__class__,
            ProviderB,
        )

    def test_selector_uses_default_for_unknown_source_type(self):
        default = ProviderA()
        registry = RetrievalProviderRegistry(default_provider=default)
        selector = RegistryRetrievalProviderSelector(registry)

        result = selector.select({"source_type": "unknown"})
        self.assertEqual(result.status, "selected")
        self.assertIs(result.provider, default)

    def test_engine_executes_selected_provider(self):
        registry = RetrievalProviderRegistry(
            providers={"live_web": ProviderB()},
            default_provider=ProviderA(),
        )
        selector = RegistryRetrievalProviderSelector(registry)
        engine = RealityRetrievalEngine(
            provider_executor=RetrievalProviderExecutor(),
            provider_selector=selector,
        )

        result = engine.retrieve(
            {"status": "ready", "request": {"query": "now", "source_type": "live_web"}}
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["provider"], "provider_b")
        self.assertEqual(result["content"], "B")

    def test_engine_keeps_not_required_retrieval_non_executing(self):
        class UnexpectedSelector:
            def select(self, request):
                raise AssertionError("selector must not run")

        engine = RealityRetrievalEngine(provider_selector=UnexpectedSelector())
        result = engine.retrieve({"status": "not_required", "request": None})

        self.assertEqual(result["status"], "not_required")
        self.assertFalse(result["retrieval_executed"])

    def test_default_dependencies_share_retrieval_selector_with_engine(self):
        dependencies = OrchestrationDependencies.default()

        self.assertIs(
            dependencies.retrieval_engine.provider_selector,
            dependencies.retrieval_provider_selector,
        )
        self.assertIs(
            dependencies.retrieval_engine.provider_executor,
            dependencies.retrieval_provider_executor,
        )


if __name__ == "__main__":
    unittest.main()
