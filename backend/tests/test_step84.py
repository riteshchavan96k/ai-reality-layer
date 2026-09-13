import unittest

from backend.app.reality.retrieval_engine import RealityRetrievalEngine
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_response import RetrievalProviderResponse
from backend.app.reality.retrieval_provider_selection import RetrievalProviderSelectionResult
from backend.app.reality.retrieval_provider_selection_decision import RetrievalProviderSelectionDecision
from backend.app.reality.retrieval_provider_selection_policy_result import (
    RetrievalProviderSelectionPolicyResult,
)


class FakeProvider:
    name = "fake-provider"

    def retrieve(self, request: RetrievalProviderRequest) -> RetrievalProviderResponse:
        return RetrievalProviderResponse(
            status="completed",
            provider=self.name,
            sources=[{"title": "Example", "url": "https://example.com"}],
            content="retrieved content",
        )


class MappingSelector:
    def __init__(self, result):
        self.result = result

    def select(self, request):
        return self.result


class TestRetrievalSelectionResultConsumption(unittest.TestCase):
    def _contract(self):
        return {
            "status": "approved",
            "request": {
                "query": "current AI news",
                "source_type": "web",
            },
        }

    def test_typed_selection_result_is_consumed(self):
        provider = FakeProvider()
        selection = RetrievalProviderSelectionResult.selected("web", provider)
        engine = RealityRetrievalEngine(provider_selector=MappingSelector(selection))

        result = engine.retrieve(self._contract())

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["provider"], provider.name)
        self.assertTrue(result["retrieval_executed"])

    def test_selected_mapping_is_normalized_and_executed(self):
        provider = FakeProvider()
        engine = RealityRetrievalEngine(
            provider_selector=MappingSelector(
                {
                    "status": "selected",
                    "source_type": "web",
                    "provider": provider,
                }
            )
        )

        result = engine.retrieve(self._contract())

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["content"], "retrieved content")

    def test_unavailable_mapping_is_normalized_and_blocks_execution(self):
        engine = RealityRetrievalEngine(
            provider_selector=MappingSelector(
                {
                    "status": "unavailable",
                    "source_type": "web",
                    "reason": "provider_unavailable",
                }
            )
        )

        result = engine.retrieve(self._contract())

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "provider_unavailable")
        self.assertFalse(result["retrieval_executed"])

    def test_nested_decision_mapping_is_normalized_before_execution(self):
        provider = FakeProvider()
        policy_result = RetrievalProviderSelectionPolicyResult.allowed_result("web")
        decision = RetrievalProviderSelectionDecision.selected("web", provider, policy_result)
        engine = RealityRetrievalEngine(
            provider_selector=MappingSelector(
                {
                    "status": "selected",
                    "source_type": "web",
                    "provider": provider,
                    "decision": decision.to_dict(),
                }
            )
        )

        result = engine.retrieve(self._contract())

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["provider"], provider.name)

    def test_invalid_selection_mapping_fails_closed(self):
        engine = RealityRetrievalEngine(
            provider_selector=MappingSelector(
                {
                    "status": "selected",
                    "source_type": "web",
                }
            )
        )

        result = engine.retrieve(self._contract())

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "invalid_provider_selection_result")
        self.assertFalse(result["retrieval_executed"])

    def test_unsupported_selection_shape_fails_closed(self):
        engine = RealityRetrievalEngine(provider_selector=MappingSelector("invalid"))

        result = engine.retrieve(self._contract())

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "invalid_provider_selection_result")
        self.assertFalse(result["retrieval_executed"])

    def test_not_required_path_is_unchanged(self):
        engine = RealityRetrievalEngine(provider_selector=MappingSelector("invalid"))

        result = engine.retrieve(
            {
                "status": "not_required",
                "request": None,
            }
        )

        self.assertEqual(result["status"], "not_required")
        self.assertFalse(result["retrieval_executed"])


if __name__ == "__main__":
    unittest.main()
