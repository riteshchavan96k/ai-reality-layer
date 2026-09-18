import unittest

from backend.app.reality.retrieval_result import RetrievalResultContract
from backend.app.reality.retrieval_result_normalizer import RetrievalResultNormalizer
from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse


class Step146RetrievalResultContractTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            "query": "current reality",
            "source_type": "live_web",
            "temporal_scope": "current",
        }

    def test_completed_result_has_canonical_execution_semantics(self):
        result = RetrievalResultContract.completed(
            self.request,
            "  http_retrieval  ",
            [{"uri": "https://example.test/source"}],
            "retrieved",
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["provider"], "http_retrieval")
        self.assertTrue(result["retrieval_executed"])
        self.assertNotIn("reason", result)

    def test_failed_result_requires_and_canonicalizes_reason(self):
        result = RetrievalResultContract.failed(
            self.request,
            "http_retrieval",
            "  upstream_failed  ",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "upstream_failed")
        self.assertTrue(result["retrieval_executed"])
        self.assertEqual(result["sources"], [])
        self.assertIsNone(result["content"])

    def test_blocked_result_does_not_claim_execution(self):
        result = RetrievalResultContract.blocked(
            self.request,
            "http_retrieval",
            "  capability_mismatch  ",
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "capability_mismatch")
        self.assertFalse(result["retrieval_executed"])
        self.assertEqual(result["sources"], [])
        self.assertIsNone(result["content"])

    def test_invalid_provider_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalResultContract.completed(self.request, "   ", [], None)

        with self.assertRaises(ValueError):
            RetrievalResultContract.failed(self.request, 123, "failed")

    def test_invalid_failure_reason_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalResultContract.failed(self.request, None, "")

        with self.assertRaises(ValueError):
            RetrievalResultContract.blocked(self.request, None, "   ")

    def test_non_completed_payload_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalResultContract.failed(
                self.request,
                None,
                "failed",
            )["sources"].append({"uri": "https://example.test/source"})

        with self.assertRaises(ValueError):
            RetrievalResultContract.blocked(
                self.request,
                None,
                "blocked",
            )["content"] = "unexpected"

    def test_result_normalizer_preserves_response_fallback_semantics(self):
        response = RetrievalProviderResponse(
            status="failed",
            reason="upstream_failed",
        )

        result = RetrievalResultNormalizer.normalize(
            self.request,
            response,
            fallback_provider="  http_retrieval  ",
        )

        self.assertEqual(result["provider"], "http_retrieval")
        self.assertEqual(result["reason"], "upstream_failed")
        self.assertTrue(result["retrieval_executed"])


if __name__ == "__main__":
    unittest.main()
