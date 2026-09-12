import unittest

from backend.app.reality.retrieval_provider_availability import RetrievalProviderAvailability
from backend.app.reality.retrieval_provider_availability_evaluation import (
    RetrievalProviderAvailabilityEvaluationResult,
)
from backend.app.reality.retrieval_provider_availability_evaluator import RetrievalProviderAvailabilityEvaluator
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_selector import RegistryRetrievalProviderSelector


class StubProvider:
    def retrieve(self, request):
        return {"status": "completed", "provider": "stub", "sources": [], "content": ""}


class RecordingAvailabilityEvaluator:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def evaluate(self, availability):
        self.calls.append(availability)
        return self.result


class Step74RetrievalProviderAvailabilityEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.provider = StubProvider()
        self.registry = RetrievalProviderRegistry()
        self.registry.register("live_web", self.provider)

    def test_available_state_is_accepted(self):
        result = RetrievalProviderAvailabilityEvaluator.evaluate(
            RetrievalProviderAvailability.available()
        )
        self.assertIsInstance(result, RetrievalProviderAvailabilityEvaluationResult)
        self.assertEqual(result.status, "available")
        self.assertTrue(result.supported)

    def test_unavailable_state_is_rejected(self):
        result = RetrievalProviderAvailabilityEvaluator.evaluate(
            RetrievalProviderAvailability.unavailable("maintenance")
        )
        self.assertEqual(result.status, "unavailable")
        self.assertFalse(result.supported)
        self.assertEqual(result.reason, "maintenance")

    def test_blocked_state_is_rejected(self):
        result = RetrievalProviderAvailabilityEvaluator.evaluate(
            RetrievalProviderAvailability.blocked("policy_blocked")
        )
        self.assertEqual(result.status, "blocked")
        self.assertFalse(result.supported)
        self.assertEqual(result.reason, "policy_blocked")

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderAvailabilityEvaluator.evaluate(object())

    def test_selector_delegates_availability_evaluation(self):
        evaluator = RecordingAvailabilityEvaluator(
            RetrievalProviderAvailabilityEvaluationResult.available_result()
        )
        selector = RegistryRetrievalProviderSelector(
            self.registry,
            availability_evaluator=evaluator,
        )
        result = selector.select({"source_type": "live_web", "query": "current reality"})
        self.assertEqual(result.status, "selected")
        self.assertEqual(len(evaluator.calls), 1)

    def test_selector_stops_when_availability_evaluation_rejects(self):
        evaluator = RecordingAvailabilityEvaluator(
            RetrievalProviderAvailabilityEvaluationResult.unavailable_result()
        )
        selector = RegistryRetrievalProviderSelector(
            self.registry,
            availability_evaluator=evaluator,
        )
        result = selector.select({"source_type": "live_web", "query": "current reality"})
        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.reason, "retrieval_provider_unavailable")
        self.assertIsNone(result.provider)
        self.assertEqual(len(evaluator.calls), 1)


if __name__ == "__main__":
    unittest.main()
