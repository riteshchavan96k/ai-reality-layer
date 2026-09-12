import unittest

from backend.app.reality.retrieval_provider_availability import RetrievalProviderAvailability
from backend.app.reality.retrieval_provider_availability_evaluation import (
    RetrievalProviderAvailabilityEvaluationResult,
)
from backend.app.reality.retrieval_provider_availability_evaluator import RetrievalProviderAvailabilityEvaluator


class Step75RetrievalProviderAvailabilityEvaluationResultTests(unittest.TestCase):
    def test_available_result_is_explicit_and_stable(self):
        result = RetrievalProviderAvailabilityEvaluator.evaluate(
            RetrievalProviderAvailability.available()
        )
        self.assertEqual(result.status, "available")
        self.assertTrue(result.supported)
        self.assertIsNone(result.reason)
        self.assertTrue(result.availability_checked)
        self.assertTrue(result.evaluation_executed)

    def test_unavailable_result_preserves_reason(self):
        result = RetrievalProviderAvailabilityEvaluator.evaluate(
            RetrievalProviderAvailability.unavailable("maintenance")
        )
        self.assertEqual(result.status, "unavailable")
        self.assertFalse(result.supported)
        self.assertEqual(result.reason, "maintenance")

    def test_blocked_result_preserves_reason(self):
        result = RetrievalProviderAvailabilityEvaluator.evaluate(
            RetrievalProviderAvailability.blocked("policy_blocked")
        )
        self.assertEqual(result.status, "blocked")
        self.assertFalse(result.supported)
        self.assertEqual(result.reason, "policy_blocked")

    def test_result_serializes_deterministically(self):
        result = RetrievalProviderAvailabilityEvaluationResult.unavailable_result("maintenance")
        self.assertEqual(
            result.to_dict(),
            {
                "status": "unavailable",
                "supported": False,
                "reason": "maintenance",
                "availability_checked": True,
                "evaluation_executed": True,
            },
        )

    def test_result_is_immutable(self):
        result = RetrievalProviderAvailabilityEvaluationResult.available_result()
        with self.assertRaises(Exception):
            result.status = "unavailable"

    def test_invalid_result_status_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderAvailabilityEvaluationResult(
                status="unknown",
                supported=False,
            )

    def test_supported_state_must_match_status(self):
        with self.assertRaises(ValueError):
            RetrievalProviderAvailabilityEvaluationResult(
                status="available",
                supported=False,
            )


if __name__ == "__main__":
    unittest.main()
