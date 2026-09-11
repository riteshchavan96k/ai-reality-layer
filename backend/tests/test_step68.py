import unittest

from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse
from backend.app.reality.retrieval_result import RetrievalResultContract
from backend.app.reality.retrieval_result_normalizer import RetrievalResultNormalizer
from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor


class TypedProvider:
    name = "typed_provider"

    def retrieve(self, request: RetrievalProviderRequest) -> RetrievalProviderResponse:
        return RetrievalProviderResponse(
            status="completed",
            provider=self.name,
            sources=({"title": "example"},),
            content=request.query,
        )


class Step68RetrievalResultNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.request = {"query": "current reality", "source_type": "live_web"}

    def test_completed_response_becomes_stable_result(self):
        response = RetrievalProviderResponse(
            status="completed",
            provider="web",
            sources=({"title": "example"},),
            content="reality",
        )

        result = RetrievalResultNormalizer.normalize(self.request, response)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["provider"], "web")
        self.assertEqual(result["sources"], [{"title": "example"}])
        self.assertEqual(result["content"], "reality")
        self.assertTrue(result["retrieval_executed"])

    def test_failed_response_preserves_failure_semantics(self):
        response = RetrievalProviderResponse(
            status="failed",
            provider="web",
            reason="provider_timeout",
        )

        result = RetrievalResultNormalizer.normalize(self.request, response)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "provider_timeout")
        self.assertTrue(result["retrieval_executed"])

    def test_blocked_response_does_not_claim_execution(self):
        response = RetrievalProviderResponse(
            status="blocked",
            provider="web",
            reason="policy_blocked",
        )

        result = RetrievalResultNormalizer.normalize(self.request, response)

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "policy_blocked")
        self.assertFalse(result["retrieval_executed"])

    def test_provider_unavailable_maps_to_blocked_result(self):
        response = RetrievalProviderResponse(
            status="provider_unavailable",
            provider="web",
        )

        result = RetrievalResultNormalizer.normalize(self.request, response)

        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["retrieval_executed"])

    def test_executor_delegates_final_result_normalization(self):
        typed_request = RetrievalProviderRequest(
            query="current reality",
            source_type="live_web",
        )

        result = RetrievalProviderExecutor().execute(TypedProvider(), typed_request)

        expected = RetrievalResultContract.completed(
            typed_request.to_dict(),
            "typed_provider",
            [{"title": "example"}],
            "current reality",
        )
        self.assertEqual(result, expected)

    def test_normalizer_rejects_non_contract_response(self):
        with self.assertRaises(ValueError):
            RetrievalResultNormalizer.normalize(self.request, {"status": "completed"})


if __name__ == "__main__":
    unittest.main()
