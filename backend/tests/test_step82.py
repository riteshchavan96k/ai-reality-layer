import unittest

from backend.app.reality.retrieval_provider_selection import RetrievalProviderSelectionResult
from backend.app.reality.retrieval_provider_selection_decision import RetrievalProviderSelectionDecision
from backend.app.reality.retrieval_provider_selection_decision_normalizer import (
    RetrievalProviderSelectionDecisionNormalizer,
)
from backend.app.reality.retrieval_provider_selection_policy_result import (
    RetrievalProviderSelectionPolicyResult,
)


class TestRetrievalProviderSelectionDecisionNormalization(unittest.TestCase):
    def setUp(self):
        self.policy_result = RetrievalProviderSelectionPolicyResult.allowed_result("web")

    def test_typed_decision_is_preserved(self):
        decision = RetrievalProviderSelectionDecision.selected("web", object(), self.policy_result)
        normalized = RetrievalProviderSelectionDecisionNormalizer.normalize(decision)
        self.assertIs(normalized, decision)

    def test_selected_mapping_is_normalized(self):
        provider = object()
        normalized = RetrievalProviderSelectionDecisionNormalizer.normalize(
            {
                "status": "selected",
                "source_type": "web",
                "provider": provider,
                "policy_result": self.policy_result.to_dict(),
            }
        )
        self.assertEqual(normalized.status, "selected")
        self.assertIs(normalized.provider, provider)
        self.assertIsInstance(normalized.policy_result, RetrievalProviderSelectionPolicyResult)

    def test_rejected_mapping_is_normalized(self):
        normalized = RetrievalProviderSelectionDecisionNormalizer.normalize(
            {
                "status": "rejected",
                "source_type": "web",
                "reason": "blocked",
                "policy_result": RetrievalProviderSelectionPolicyResult.rejected_result(
                    "web", "blocked"
                ).to_dict(),
            }
        )
        self.assertEqual(normalized.status, "rejected")
        self.assertEqual(normalized.reason, "blocked")
        self.assertIsNone(normalized.provider)

    def test_unsupported_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderSelectionDecisionNormalizer.normalize("invalid")

    def test_invalid_mapping_is_rejected(self):
        with self.assertRaises((KeyError, ValueError)):
            RetrievalProviderSelectionDecisionNormalizer.normalize(
                {"status": "selected", "source_type": "web"}
            )

    def test_result_normalizes_mapping_decision(self):
        provider = object()
        result = RetrievalProviderSelectionResult.selected(
            "web",
            provider,
            {
                "status": "selected",
                "source_type": "web",
                "provider": provider,
                "policy_result": self.policy_result.to_dict(),
            },
        )
        self.assertIsInstance(result.decision, RetrievalProviderSelectionDecision)
        self.assertIs(result.decision.provider, provider)

    def test_result_rejects_inconsistent_decision(self):
        decision = RetrievalProviderSelectionDecision.rejected("web", "blocked")
        with self.assertRaises(ValueError):
            RetrievalProviderSelectionResult.selected("web", object(), decision)

    def test_result_rejects_selected_decision_for_unavailable_result(self):
        decision = RetrievalProviderSelectionDecision.selected("web", object())
        with self.assertRaises(ValueError):
            RetrievalProviderSelectionResult.unavailable("web", "blocked", decision)


if __name__ == "__main__":
    unittest.main()
