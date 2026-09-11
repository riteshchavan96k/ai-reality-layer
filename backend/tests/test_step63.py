import unittest

from backend.app.reality.retrieval_engine import RealityRetrievalEngine
from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_selection import RetrievalProviderSelectionResult
from backend.app.reality.retrieval_provider_selector import RegistryRetrievalProviderSelector


class Provider:
    name = "test_provider"

    def retrieve(self, request):
        return {"status": "completed", "provider": self.name, "sources": [], "content": "ok"}


class Step63RetrievalProviderSelectionResultTests(unittest.TestCase):
    def test_selected_result_contains_provider_and_execution_state(self):
        provider = Provider()
        result = RetrievalProviderSelectionResult.selected("live_web", provider)

        self.assertEqual(result.status, "selected")
        self.assertEqual(result.source_type, "live_web")
        self.assertIs(result.provider, provider)
        self.assertTrue(result.selection_executed)
        self.assertIsNone(result.reason)

    def test_unavailable_result_is_non_executing(self):
        result = RetrievalProviderSelectionResult.unavailable("live_web")

        self.assertEqual(result.status, "unavailable")
        self.assertFalse(result.selection_executed)
        self.assertIsNone(result.provider)
        self.assertEqual(result.reason, "retrieval_provider_unavailable")

    def test_selector_returns_stable_result(self):
        provider = Provider()
        selector = RegistryRetrievalProviderSelector(
            RetrievalProviderRegistry(default_provider=provider)
        )

        result = selector.select({"source_type": "live_web"})

        self.assertIsInstance(result, RetrievalProviderSelectionResult)
        self.assertIs(result.provider, provider)

    def test_engine_blocks_when_selection_is_unavailable(self):
        class EmptySelector:
            def select(self, request):
                return RetrievalProviderSelectionResult.unavailable(
                    request["source_type"],
                    "no_provider_registered",
                )

        class UnexpectedExecutor:
            def execute(self, provider, request):
                raise AssertionError("provider execution must not run")

        engine = RealityRetrievalEngine(
            provider_executor=UnexpectedExecutor(),
            provider_selector=EmptySelector(),
        )

        result = engine.retrieve(
            {"status": "ready", "request": {"query": "x", "source_type": "live_web"}}
        )

        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["retrieval_executed"])
        self.assertEqual(result["reason"], "no_provider_registered")

    def test_selected_provider_still_executes_through_executor(self):
        provider = Provider()
        selector = RegistryRetrievalProviderSelector(
            RetrievalProviderRegistry(default_provider=provider)
        )
        engine = RealityRetrievalEngine(
            provider_executor=RetrievalProviderExecutor(),
            provider_selector=selector,
        )

        result = engine.retrieve(
            {"status": "ready", "request": {"query": "x", "source_type": "live_web"}}
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["content"], "ok")


if __name__ == "__main__":
    unittest.main()
