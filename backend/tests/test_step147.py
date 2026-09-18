import unittest

from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse
from backend.app.reality.retrieval_result_normalizer import RetrievalResultNormalizer


class Step147RetrievalResultStatusTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            "query": "current reality",
            "source_type": "live_web",
            "temporal_scope": "current",
        }

    def test_completed_status_maps_only_to_completed_result(self):
        response = RetrievalProviderResponse(
            status="completed",
            provider="http_retrieval",
            sources=({"uri": "https://example.test/source"},),
            content="retrieved",
        )

        result = RetrievalResultNormalizer.normalize(self.request, response)

        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["retrieval_executed"])

    def test_failed_status_maps_only_to_failed_result(self):
        response = RetrievalProviderResponse(
            status="failed",
            provider="http_retrieval",
            reason="upstream_failed",
        )

        result = RetrievalResultNormalizer.normalize(self.request, response)

        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["retrieval_executed"])
        self.assertEqual(result["reason"], "upstream_failed")

    def test_blocked_status_maps_to_blocked_result(self):
        response = RetrievalProviderResponse(
            status="blocked",
            provider="http_retrieval",
            reason="policy_blocked",
        )

        result = RetrievalResultNormalizer.normalize(self.request, response)

        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["retrieval_executed"])

    def test_provider_unavailable_maps_to_blocked_result(self):
        response = RetrievalProviderResponse(
            status="provider_unavailable",
            provider="http_retrieval",
            reason="provider_unavailable",
        )

        result = RetrievalResultNormalizer.normalize(self.request, response)

        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["retrieval_executed"])
        self.assertEqual(result["reason"], "provider_unavailable")

    def test_unsupported_status_cannot_fall_through_to_completed(self):
        response = object.__new__(RetrievalProviderResponse)
        object.__setattr__(response, "status", "future_status")
        object.__setattr__(response, "provider", "http_retrieval")
        object.__setattr__(response, "sources", ())
        object.__setattr__(response, "content", None)
        object.__setattr__(response, "reason", "future_reason")

        with self.assertRaisesRegex(
            ValueError,
            "unsupported retrieval provider response status",
        ):
            RetrievalResultNormalizer.normalize(self.request, response)


if __name__ == "__main__":
    unittest.main()
