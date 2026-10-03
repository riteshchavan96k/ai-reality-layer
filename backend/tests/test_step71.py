import unittest

from backend.app.reality.retrieval_provider_capabilities import RetrievalProviderCapabilities
from backend.app.reality.retrieval_provider_capability_evaluator import RetrievalProviderCapabilityEvaluator
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest


class Step71CapabilityEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.capabilities = RetrievalProviderCapabilities(
            source_types=("live_web",),
            temporal_scopes=("current",),
        )
        self.evaluator = RetrievalProviderCapabilityEvaluator()

    def test_evaluator_accepts_matching_request(self):
        request = RetrievalProviderRequest(
            query="current reality",
            source_type="live_web",
            temporal_scope="current",
        )
        result = self.evaluator.evaluate(self.capabilities, request)
        self.assertTrue(result.supported)
        self.assertEqual(result.status, "supported")

    def test_evaluator_rejects_temporal_mismatch(self):
        request = RetrievalProviderRequest(
            query="historical reality",
            source_type="live_web",
            temporal_scope="historical",
        )
        result = self.evaluator.evaluate(self.capabilities, request)
        self.assertFalse(result.supported)
        self.assertEqual(result.status, "unsupported")

    def test_evaluator_rejects_source_type_mismatch(self):
        request = RetrievalProviderRequest(
            query="current reality",
            source_type="database",
            temporal_scope="current",
        )
        result = self.evaluator.evaluate(self.capabilities, request)
        self.assertFalse(result.supported)
        self.assertEqual(result.status, "unsupported")

    def test_evaluator_rejects_invalid_capabilities(self):
        request = RetrievalProviderRequest(
            query="current reality",
            source_type="live_web",
            temporal_scope="current",
        )
        with self.assertRaises(ValueError):
            self.evaluator.evaluate(object(), request)

    def test_evaluator_rejects_invalid_request(self):
        with self.assertRaises(ValueError):
            self.evaluator.evaluate(self.capabilities, object())


if __name__ == "__main__":
    unittest.main()
