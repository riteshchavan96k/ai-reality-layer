import unittest
from unittest.mock import Mock

from backend.app.reality.retrieval_provider_health_contract import RetrievalProviderHealth
from backend.app.reality.retrieval_provider_health_evaluation import RetrievalProviderHealthEvaluationResult
from backend.app.reality.retrieval_provider_health_evaluator import RetrievalProviderHealthEvaluator
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_selector import RegistryRetrievalProviderSelector


class StubProvider:
    provider_name = "live_web"

    def retrieve(self, request):
        return {"status": "completed", "sources": [], "content": "ok", "provider": self.provider_name}


class Step77RetrievalProviderHealthEvaluationTests(unittest.TestCase):
    def test_healthy_provider_is_accepted(self):
        health = RetrievalProviderHealth.healthy("live_web")
        result = RetrievalProviderHealthEvaluator.evaluate(health)
        self.assertIsInstance(result, RetrievalProviderHealthEvaluationResult)
        self.assertTrue(result.supported)

    def test_unhealthy_provider_is_rejected(self):
        health = RetrievalProviderHealth.unhealthy("live_web", "timeout")
        result = RetrievalProviderHealthEvaluator.evaluate(health)
        self.assertFalse(result.supported)
        self.assertEqual(result.reason, "timeout")

    def test_unknown_provider_is_rejected(self):
        health = RetrievalProviderHealth.unknown("live_web")
        result = RetrievalProviderHealthEvaluator.evaluate(health)
        self.assertFalse(result.supported)
        self.assertEqual(result.reason, "retrieval_provider_health_unknown")

    def test_invalid_health_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderHealthEvaluator.evaluate("healthy")

    def test_registry_defaults_to_healthy_for_compatibility(self):
        registry = RetrievalProviderRegistry()
        registry.register("live_web", StubProvider())
        health = registry.get_health("live_web")
        self.assertEqual(health.provider, "live_web")
        self.assertEqual(health.status, "healthy")

    def test_registry_preserves_explicit_health(self):
        registry = RetrievalProviderRegistry()
        registry.register("live_web", StubProvider())
        registry.register_health("live_web", RetrievalProviderHealth.unhealthy("live_web", "maintenance"))
        health = registry.get_health("live_web")
        self.assertEqual(health.status, "unhealthy")
        self.assertEqual(health.reason, "maintenance")

    def test_registry_clears_health_when_provider_is_replaced(self):
        registry = RetrievalProviderRegistry()
        registry.register("live_web", StubProvider())
        registry.register_health("live_web", RetrievalProviderHealth.unhealthy("live_web", "maintenance"))
        registry.register("live_web", StubProvider())
        self.assertEqual(registry.get_health("live_web").status, "healthy")

    def test_selector_stops_when_health_evaluation_rejects(self):
        registry = RetrievalProviderRegistry()
        registry.register("live_web", StubProvider())
        registry.register_health("live_web", RetrievalProviderHealth.unhealthy("live_web", "maintenance"))
        health_evaluator = Mock()
        health_evaluator.evaluate.return_value = RetrievalProviderHealthEvaluationResult.unhealthy(
            RetrievalProviderHealth.unhealthy("live_web", "maintenance")
        )
        selector = RegistryRetrievalProviderSelector(registry, health_evaluator=health_evaluator)

        result = selector.select({"source_type": "live_web", "query": "current status"})

        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.reason, "maintenance")
        health_evaluator.evaluate.assert_called_once()

    def test_selector_allows_healthy_provider(self):
        registry = RetrievalProviderRegistry()
        registry.register("live_web", StubProvider())
        health_evaluator = Mock()
        health_evaluator.evaluate.return_value = RetrievalProviderHealthEvaluationResult.healthy(
            RetrievalProviderHealth.healthy("live_web")
        )
        selector = RegistryRetrievalProviderSelector(registry, health_evaluator=health_evaluator)

        result = selector.select({"source_type": "live_web", "query": "current status"})

        self.assertEqual(result.status, "selected")
        health_evaluator.evaluate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
