import unittest

from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse
from backend.app.reality.retrieval_result_normalizer import RetrievalResultNormalizer


class Step144ProviderIdentityContractTests(unittest.TestCase):
    def setUp(self):
        self.request = {"query": "current reality", "source_type": "live_web"}

    def test_provider_identity_is_trimmed_to_canonical_value(self):
        response = RetrievalProviderResponse(
            status="completed",
            provider="  http_retrieval  ",
            content="retrieved",
        )

        self.assertEqual(response.provider, "http_retrieval")
        self.assertEqual(response.to_dict()["provider"], "http_retrieval")

    def test_blank_provider_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderResponse(provider="")

        with self.assertRaises(ValueError):
            RetrievalProviderResponse(provider="   ")

    def test_non_string_provider_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderResponse(provider=123)

    def test_missing_provider_identity_remains_available_for_executor_fallback(self):
        response = RetrievalProviderResponse(
            status="completed",
            content="retrieved",
        )

        result = RetrievalResultNormalizer.normalize(
            self.request,
            response,
            fallback_provider="http_retrieval",
        )

        self.assertEqual(result["provider"], "http_retrieval")

    def test_response_provider_identity_takes_precedence_over_fallback(self):
        response = RetrievalProviderResponse(
            status="completed",
            provider="declared_provider",
            content="retrieved",
        )

        result = RetrievalResultNormalizer.normalize(
            self.request,
            response,
            fallback_provider="executor_provider",
        )

        self.assertEqual(result["provider"], "declared_provider")


if __name__ == "__main__":
    unittest.main()
