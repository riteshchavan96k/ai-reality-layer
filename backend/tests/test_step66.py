import unittest

from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse


class ResponseProvider:
    name = "response_provider"

    def retrieve(self, request: RetrievalProviderRequest) -> RetrievalProviderResponse:
        return RetrievalProviderResponse(
            status="completed",
            provider=self.name,
            sources=({"title": "example"},),
            content=request.query,
        )


class MappingProvider:
    name = "mapping_provider"

    def retrieve(self, request: RetrievalProviderRequest):
        return {
            "status": "completed",
            "provider": self.name,
            "sources": [],
            "content": request.query,
        }


class Step66RetrievalProviderResponseTests(unittest.TestCase):
    def test_response_validates_and_round_trips(self):
        response = RetrievalProviderResponse(
            status="completed",
            provider="web",
            sources=({"url": "example"},),
            content="reality",
        )

        self.assertEqual(
            RetrievalProviderResponse.from_mapping(response.to_dict()),
            response,
        )
        self.assertEqual(response.sources, ({"url": "example"},))

    def test_invalid_response_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderResponse(status="unknown")

        with self.assertRaises(ValueError):
            RetrievalProviderResponse(sources=[{"url": "example"}])

        with self.assertRaises(ValueError):
            RetrievalProviderResponse(sources=("invalid",))

        with self.assertRaises(ValueError):
            RetrievalProviderResponse(content=123)

    def test_provider_protocol_accepts_typed_response_provider(self):
        self.assertIsInstance(ResponseProvider(), RetrievalProvider)

    def test_executor_accepts_typed_response(self):
        request = RetrievalProviderRequest(query="current reality", source_type="live_web")

        result = RetrievalProviderExecutor().execute(ResponseProvider(), request)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["provider"], "response_provider")
        self.assertEqual(result["content"], "current reality")
        self.assertEqual(result["sources"], [{"title": "example"}])

    def test_executor_preserves_legacy_mapping_compatibility(self):
        request = RetrievalProviderRequest(query="hello", source_type="live_web")

        result = RetrievalProviderExecutor().execute(MappingProvider(), request)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["content"], "hello")

    def test_failure_and_blocked_statuses_remain_stable(self):
        request = RetrievalProviderRequest(query="hello", source_type="live_web")

        class BlockedProvider:
            def retrieve(self, request):
                return RetrievalProviderResponse(status="blocked", reason="provider_unavailable")

        class FailedProvider:
            def retrieve(self, request):
                return RetrievalProviderResponse(status="failed", reason="upstream_failed")

        blocked = RetrievalProviderExecutor().execute(BlockedProvider(), request)
        failed = RetrievalProviderExecutor().execute(FailedProvider(), request)

        self.assertEqual(blocked["status"], "blocked")
        self.assertFalse(blocked["retrieval_executed"])
        self.assertEqual(blocked["reason"], "provider_unavailable")
        self.assertEqual(failed["status"], "failed")
        self.assertTrue(failed["retrieval_executed"])
        self.assertEqual(failed["reason"], "upstream_failed")


if __name__ == "__main__":
    unittest.main()
