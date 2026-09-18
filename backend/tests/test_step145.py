import unittest

from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse
from backend.app.reality.retrieval_result_normalizer import RetrievalResultNormalizer


class Step145ProviderReasonContractTests(unittest.TestCase):
    def setUp(self):
        self.request = {"query": "current reality", "source_type": "live_web"}

    def test_reason_is_trimmed_to_canonical_value(self):
        response = RetrievalProviderResponse(
            status="failed",
            reason="  upstream_failed  ",
        )

        self.assertEqual(response.reason, "upstream_failed")
        self.assertEqual(response.to_dict()["reason"], "upstream_failed")

    def test_empty_reason_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderResponse(reason="")

        with self.assertRaises(ValueError):
            RetrievalProviderResponse(reason="   ")

    def test_non_string_reason_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderResponse(reason=123)

    def test_missing_reason_remains_optional(self):
        response = RetrievalProviderResponse(status="failed")

        self.assertIsNone(response.reason)

        result = RetrievalResultNormalizer.normalize(
            self.request,
            response,
            fallback_provider="http_retrieval",
        )
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "retrieval_provider_failed")

    def test_canonical_reason_survives_result_normalization(self):
        response = RetrievalProviderResponse(
            status="blocked",
            reason="  upstream_blocked  ",
        )

        result = RetrievalResultNormalizer.normalize(
            self.request,
            response,
            fallback_provider="http_retrieval",
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "upstream_blocked")


if __name__ == "__main__":
    unittest.main()
