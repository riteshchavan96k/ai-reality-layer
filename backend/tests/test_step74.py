import unittest

from backend.app.reality.retrieval_provider_availability import RetrievalProviderAvailability
from backend.app.reality.retrieval_provider_availability_evaluator import RetrievalProviderAvailabilityEvaluator


class Step74RetrievalProviderAvailabilityEvaluationTests(unittest.TestCase):
    def test_available_state_is_accepted(self):
        result = RetrievalProviderAvailabilityEvaluator.evaluate(
            RetrievalProviderAvailability.available()
        )
        self.assertTrue(result)

    def test_unavailable_state_is_rejected(self):
        result = RetrievalProviderAvailabilityEvaluator.evaluate(
            RetrievalProviderAvailability.unavailable("maintenance")
        )
        self.assertFalse(result)

    def test_blocked_state_is_rejected(self):
        result = RetrievalProviderAvailabilityEvaluator.evaluate(
            RetrievalProviderAvailability.blocked("policy_blocked")
        )
        self.assertFalse(result)

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderAvailabilityEvaluator.evaluate(object())


if __name__ == "__main__":
    unittest.main()
