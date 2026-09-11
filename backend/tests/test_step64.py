import unittest

from backend.app.reality.retrieval_engine import RealityRetrievalEngine
from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_selection import RetrievalProviderSelectionResult


class Provider:
    name = "test_provider"

    def retrieve(self, request):
        return {
            "status": "completed",
            "provider": self.name,
            "sources": [],
            "content": "ok",
        }


class InvalidProvider:
    pass


class Step64RetrievalProviderContractTests(unittest.TestCase):
    def test_valid_provider_satisfies_shared_contract(self):
        self.assertTrue(isinstance(Provider(), RetrievalProvider))

    def test_invalid_provider_does_not_satisfy_shared_contract(self):
        self.assertFalse(isinstance(InvalidProvider(), RetrievalProvider))

    def test_registry_uses_shared_provider_contract(self):
        provider = Provider()
        registry = RetrievalProviderRegistry(default_provider=provider)

        selected = registry.get("live_web")

        self.assertIs(selected, provider)
        self.assertTrue(isinstance(selected, RetrievalProvider))

    def test_selection_result_carries_contract_typed_provider(self):
        provider = Provider()
        result = RetrievalProviderSelectionResult.selected("live_web", provider)

        self.assertIs(result.provider, provider)
        self.assertTrue(isinstance(result.provider, RetrievalProvider))

    def test_executor_accepts_contract_provider_without_changing_result(self):
        result = RetrievalProviderExecutor().execute(
            Provider(),
            {"query": "x", "source_type": "live_web"},
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["content"], "ok")

    def test_engine_accepts_provider_through_existing_injection(self):
        result = RealityRetrievalEngine(provider=Provider()).retrieve(
            {
                "status": "ready",
                "request": {"query": "x", "source_type": "live_web"},
            }
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["content"], "ok")


if __name__ == "__main__":
    unittest.main()
