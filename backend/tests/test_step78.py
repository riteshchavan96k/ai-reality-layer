import unittest

from backend.app.reality.retrieval_provider_health_contract import RetrievalProviderHealth
from backend.app.reality.retrieval_provider_health_evaluation import RetrievalProviderHealthEvaluationResult
from backend.app.reality.retrieval_provider_health_evaluator import RetrievalProviderHealthEvaluator


class Step78RetrievalProviderHealthEvaluationResultTests(unittest.TestCase):
    def test_healthy_evaluation_is_explicitly_supported(self):
        health = RetrievalProviderHealth.healthy("live_web")
        result = RetrievalProviderHealthEvaluator.evaluate(health)

        self.assertIsInstance(result, RetrievalProviderHealthEvaluationResult)
        self.assertEqual(result.status, "healthy")
        self.assertTrue(result.supported)
        self.assertTrue(result.health_checked)
        self.assertTrue(result.evaluation_executed)
        self.assertIsNone(result.reason)

    def test_unhealthy_evaluation_preserves_reason(self):
        health = RetrievalProviderHealth.unhealthy("live_web", "timeout")
        result = RetrievalProviderHealthEvaluator.evaluate(health)

        self.assertEqual(result.status, "unhealthy")
        self.assertFalse(result.supported)
        self.assertEqual(result.reason, "timeout")
        self.assertTrue(result.health_checked)
        self.assertTrue(result.evaluation_executed)

    def test_unknown_evaluation_preserves_default_reason(self):
        health = RetrievalProviderHealth.unknown("live_web")
        result = RetrievalProviderHealthEvaluator.evaluate(health)

        self.assertEqual(result.status, "unknown")
        self.assertFalse(result.supported)
        self.assertEqual(result.reason, "retrieval_provider_health_unknown")

    def test_serialization_is_stable(self):
        health = RetrievalProviderHealth.unhealthy("live_web", "maintenance")
        result = RetrievalProviderHealthEvaluator.evaluate(health)

        self.assertEqual(
            result.to_dict(),
            {
                "provider": "live_web",
                "status": "unhealthy",
                "supported": False,
                "reason": "maintenance",
                "health_checked": True,
                "evaluation_executed": True,
            },
        )

    def test_result_is_immutable(self):
        result = RetrievalProviderHealthEvaluator.evaluate(
            RetrievalProviderHealth.healthy("live_web")
        )
        with self.assertRaises(Exception):
            result.supported = False

    def test_invalid_result_combinations_are_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderHealthEvaluationResult(
                provider="live_web",
                status="healthy",
                supported=False,
                reason=None,
                health_checked=True,
            )

    def test_invalid_health_input_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderHealthEvaluator.evaluate("healthy")


if __name__ == "__main__":
    unittest.main()
