import unittest

from backend.app.reality.retrieval_provider_capabilities import RetrievalProviderCapabilities
from backend.app.reality.retrieval_provider_capability_evaluation import RetrievalProviderCapabilityEvaluationResult
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest


class Step72CapabilityEvaluationResultTests(unittest.TestCase):
    def setUp(self):
        self.request = RetrievalProviderRequest("current reality", "live_web", "current")

    def test_supported_result_is_stable(self):
        result = RetrievalProviderCapabilityEvaluationResult.supported_result(self.request)
        self.assertEqual(result.status, "supported")
        self.assertTrue(result.supported)
        self.assertTrue(result.evaluation_executed)

    def test_unsupported_result_preserves_reason(self):
        result = RetrievalProviderCapabilityEvaluationResult.unsupported_result(self.request)
        self.assertEqual(result.status, "unsupported")
        self.assertFalse(result.supported)
        self.assertEqual(result.reason, "retrieval_provider_capability_mismatch")

    def test_result_serializes(self):
        result = RetrievalProviderCapabilityEvaluationResult.supported_result(self.request)
        data = result.to_dict()
        self.assertEqual(data["source_type"], "live_web")
        self.assertEqual(data["temporal_scope"], "current")
        self.assertTrue(data["evaluation_executed"])

    def test_result_is_immutable(self):
        result = RetrievalProviderCapabilityEvaluationResult.supported_result(self.request)
        with self.assertRaises(Exception):
            result.supported = False


if __name__ == "__main__":
    unittest.main()
