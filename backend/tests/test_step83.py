import unittest

from backend.app.reality.retrieval_provider_selection import RetrievalProviderSelectionResult
from backend.app.reality.retrieval_provider_selection_decision import RetrievalProviderSelectionDecision
from backend.app.reality.retrieval_provider_selection_result_normalizer import (
    RetrievalProviderSelectionResultNormalizer,
)
from backend.app.reality.retrieval_provider_selection_policy_result import (
    RetrievalProviderSelectionPolicyResult,
)


class TestRetrievalProviderSelectionResultNormalization(unittest.TestCase):
    def setUp(self):
        self.policy_result = RetrievalProviderSelectionPolicyResult.allowed_result("web")

    def test_typed_result_is_preserved(self):
        provider = object()
        result = RetrievalProviderSelectionResult.selected("web", provider)
        normalized = RetrievalProviderSelectionResultNormalizer.normalize(result)
        self.assertIs(normalized, result)

    def test_selected_mapping_is_normalized(self):
        provider = object()
        normalized = RetrievalProviderSelectionResultNormalizer.normalize(
            {
                "status": "selected",
                "source_type": "web",
                "provider": provider,
            }
        )
        self.assertIsInstance(normalized, RetrievalProviderSelectionResult)
        self.assertEqual(normalized.status, "selected")
        self.assertEqual(normalized.source_type, "web")
        self.assertIs(normalized.provider, provider)

    def test_unavailable_mapping_is_normalized(self):
        normalized = RetrievalProviderSelectionResultNormalizer.normalize(
            {
                "status": "unavailable",
                "source_type": "web",
                "reason": "provider_unavailable",
            }
        )
        self.assertEqual(normalized.status, "unavailable")
        self.assertEqual(normalized.reason, "provider_unavailable")
        self.assertIsNone(normalized.provider)

    def test_nested_decision_mapping_is_normalized(self):
        provider = object()
        normalized = RetrievalProviderSelectionResultNormalizer.normalize(
            {
                "status": "selected",
                "source_type": "web",
                "provider": provider,
                "decision": {
                    "status": "selected",
                    "source_type": "web",
                    "provider": provider,
                    "policy_result": self.policy_result.to_dict(),
                },
            }
        )
        self.assertIsInstance(normalized.decision, RetrievalProviderSelectionDecision)
        self.assertIsInstance(normalized.decision.policy_result, RetrievalProviderSelectionPolicyResult)
        self.assertIs(normalized.decision.provider, provider)

    def test_rejected_nested_decision_mapping_is_normalized(self):
        normalized = RetrievalProviderSelectionResultNormalizer.normalize(
            {
                "status": "unavailable",
                "source_type": "web",
                "reason": "blocked",
                "decision": {
                    "status": "rejected",
                    "source_type": "web",
                    "reason": "blocked",
                    "policy_result": RetrievalProviderSelectionPolicyResult.rejected_result(
                        "web", "blocked"
                    ).to_dict(),
                },
            }
        )
        self.assertEqual(normalized.decision.status, "rejected")
        self.assertEqual(normalized.decision.reason, "blocked")

    def test_unsupported_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderSelectionResultNormalizer.normalize("invalid")

    def test_invalid_mapping_is_rejected(self):
        with self.assertRaises((KeyError, ValueError)):
            RetrievalProviderSelectionResultNormalizer.normalize(
                {"status": "selected", "source_type": "web"}
            )

    def test_inconsistent_nested_decision_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderSelectionResultNormalizer.normalize(
                {
                    "status": "selected",
                    "source_type": "web",
                    "provider": object(),
                    "decision": {
                        "status": "rejected",
                        "source_type": "web",
                        "reason": "blocked",
                    },
                }
            )


if __name__ == "__main__":
    unittest.main()
