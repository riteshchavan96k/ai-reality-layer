import unittest

from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse
from backend.app.reality.retrieval_provider_response_normalizer import (
    RetrievalProviderResponseNormalizer,
)


class TypedProvider:
    name = "typed_provider"

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


class Step67RetrievalProviderResponseNormalizationTests(unittest.TestCase):
    def test_normalizer_preserves_typed_response(self):
        response = RetrievalProviderResponse(
            status="completed",
            provider="web",
            sources=({"title": "example"},),
            content="reality",
        )

        normalized = RetrievalProviderResponseNormalizer.normalize(response)

        self.assertIs(normalized, response)

    def test_normalizer_converts_legacy_mapping(self):
        normalized = RetrievalProviderResponseNormalizer.normalize(
            {
                "status": "completed",
                "provider": "web",
                "sources": [],
                "content": "reality",
            }
        )

        self.assertIsInstance(normalized, RetrievalProviderResponse)
        self.assertEqual(normalized.provider, "web")
        self.assertEqual(normalized.content, "reality")

    def test_normalizer_rejects_invalid_provider_output(self):
        with self.assertRaises(ValueError):
            RetrievalProviderResponseNormalizer.normalize(["invalid"])

    def test_executor_uses_normalizer_for_typed_response(self):
        request = RetrievalProviderRequest(query="current reality", source_type="live_web")

        result = RetrievalProviderExecutor().execute(TypedProvider(), request)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["provider"], "typed_provider")
        self.assertEqual(result["content"], "current reality")
        self.assertEqual(result["sources"], [{"title": "example"}])

    def test_executor_keeps_legacy_mapping_compatibility_through_normalizer(self):
        request = RetrievalProviderRequest(query="hello", source_type="live_web")

        result = RetrievalProviderExecutor().execute(MappingProvider(), request)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["provider"], "mapping_provider")
        self.assertEqual(result["content"], "hello")


if __name__ == "__main__":
    unittest.main()
