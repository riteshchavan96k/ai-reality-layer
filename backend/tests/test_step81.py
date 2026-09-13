import unittest

from backend.app.reality.retrieval_provider_selection import RetrievalProviderSelectionResult
from backend.app.reality.retrieval_provider_selection_decision import RetrievalProviderSelectionDecision
from backend.app.reality.retrieval_provider_selection_policy_result import RetrievalProviderSelectionPolicyResult


class TestRetrievalProviderSelectionDecision(unittest.TestCase):
    def setUp(self):
        self.policy_result = RetrievalProviderSelectionPolicyResult.allowed_result("web")

    def test_selected_decision_requires_provider(self):
        provider = object()
        decision = RetrievalProviderSelectionDecision.selected("web", provider, self.policy_result)
        self.assertEqual(decision.status, "selected")
        self.assertIs(decision.provider, provider)
        self.assertTrue(decision.selection_decided)

    def test_rejected_decision_has_no_provider(self):
        policy_result = RetrievalProviderSelectionPolicyResult.rejected_result("web", "blocked")
        decision = RetrievalProviderSelectionDecision.rejected("web", "blocked", policy_result)
        self.assertEqual(decision.status, "rejected")
        self.assertIsNone(decision.provider)
        self.assertEqual(decision.reason, "blocked")

    def test_policy_result_is_preserved(self):
        decision = RetrievalProviderSelectionDecision.selected("web", object(), self.policy_result)
        self.assertIs(decision.policy_result, self.policy_result)

    def test_serialization_is_deterministic(self):
        decision = RetrievalProviderSelectionDecision.rejected("web", "blocked", self.policy_result)
        self.assertEqual(
            decision.to_dict(),
            {
                "status": "rejected",
                "source_type": "web",
                "provider": None,
                "reason": "blocked",
                "policy_result": self.policy_result.to_dict(),
                "selection_decided": True,
            },
        )

    def test_decision_is_immutable(self):
        decision = RetrievalProviderSelectionDecision.selected("web", object())
        with self.assertRaises(AttributeError):
            decision.status = "rejected"

    def test_invalid_status_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderSelectionDecision("unknown", "web")

    def test_selected_requires_provider(self):
        with self.assertRaises(ValueError):
            RetrievalProviderSelectionDecision("selected", "web")

    def test_rejected_cannot_contain_provider(self):
        with self.assertRaises(ValueError):
            RetrievalProviderSelectionDecision("rejected", "web", provider=object())

    def test_selection_result_carries_decision(self):
        provider = object()
        decision = RetrievalProviderSelectionDecision.selected("web", provider, self.policy_result)
        result = RetrievalProviderSelectionResult.selected("web", provider, decision)
        self.assertIs(result.decision, decision)
        self.assertEqual(result.status, "selected")


if __name__ == "__main__":
    unittest.main()
