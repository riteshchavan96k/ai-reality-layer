import unittest

from backend.app.reality.retrieval_engine import RealityRetrievalEngine
from backend.app.reality.retrieval_provider import RetrievalProvider
from backend.app.reality.retrieval_provider_executor import RetrievalProviderExecutor
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_selector import RegistryRetrievalProviderSelector


class TypedProvider:
    name = "typed_provider"

    def retrieve(self, request: RetrievalProviderRequest):
        if not isinstance(request, RetrievalProviderRequest):
            raise AssertionError("provider must receive RetrievalProviderRequest")
        return {
            "status": "completed",
            "provider": self.name,
            "sources": [],
            "content": request.query,
        }


class InvalidProvider:
    pass


class Step65RetrievalProviderRequestTests(unittest.TestCase):
    def test_request_validates_and_round_trips(self):
        request = RetrievalProviderRequest(
            query="latest information",
            source_type="live_web",
            temporal_scope="current",
            required=True,
        )

        self.assertEqual(
            request.to_dict(),
            {
                "query": "latest information",
                "source_type": "live_web",
                "temporal_scope": "current",
                "required": True,
            },
        )
        self.assertEqual(
            RetrievalProviderRequest.from_mapping(request.to_dict()),
            request,
        )

    def test_invalid_request_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderRequest(query="", source_type="live_web")

        with self.assertRaises(ValueError):
            RetrievalProviderRequest(query="x", source_type="")

        with self.assertRaises(ValueError):
            RetrievalProviderRequest(query="x", source_type="web", required="yes")

    def test_provider_protocol_accepts_structural_implementation(self):
        self.assertIsInstance(TypedProvider(), RetrievalProvider)
        self.assertFalse(isinstance(InvalidProvider(), RetrievalProvider))

    def test_executor_passes_typed_request_to_provider(self):
        provider = TypedProvider()
        request = RetrievalProviderRequest(query="hello", source_type="live_web")

        result = RetrievalProviderExecutor().execute(provider, request)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["content"], "hello")
        self.assertEqual(result["request"], request.to_dict())

    def test_engine_converts_retrieval_contract_to_typed_provider_request(self):
        provider = TypedProvider()
        selector = RegistryRetrievalProviderSelector(
            RetrievalProviderRegistry(default_provider=provider)
        )
        engine = RealityRetrievalEngine(
            provider_executor=RetrievalProviderExecutor(),
            provider_selector=selector,
        )

        result = engine.retrieve(
            {
                "status": "ready",
                "request": {
                    "query": "current reality",
                    "source_type": "live_web",
                    "temporal_scope": "current",
                    "required": True,
                },
            }
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["content"], "current reality")


if __name__ == "__main__":
    unittest.main()
