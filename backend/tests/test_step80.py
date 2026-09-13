import unittest

from backend.app.reality.retrieval_provider_availability_evaluation import RetrievalProviderAvailabilityEvaluationResult
from backend.app.reality.retrieval_provider_capability_evaluation import RetrievalProviderCapabilityEvaluationResult
from backend.app.reality.retrieval_provider_health_evaluation import RetrievalProviderHealthEvaluationResult
from backend.app.reality.retrieval_provider_selection_policy import DefaultRetrievalProviderSelectionPolicy, RetrievalProviderSelectionPolicy
from backend.app.reality.retrieval_provider_selection_policy_result import RetrievalProviderSelectionPolicyResult


class Step80RetrievalProviderSelectionPolicyResultTests(unittest.TestCase):
    def setUp(self):
        self.policy = DefaultRetrievalProviderSelectionPolicy()
        self.availability = RetrievalProviderAvailabilityEvaluationResult.available_result()
        self.health = RetrievalProviderHealthEvaluationResult.healthy(
            type("Health", (), {"provider": "live_web", "reason": None, "health_checked": True})()
        )
        self.capability = RetrievalProviderCapabilityEvaluationResult.supported_result(
            type("Request", (), {"source_type": "live_web", "temporal_scope": "current"})()
        )

    def test_policy_contract_is_satisfied(self):
        self.assertIsInstance(self.policy, RetrievalProviderSelectionPolicy)

    def test_allowed_result_is_stable(self):
        result = self.policy.evaluate("live_web", self.availability, self.health, self.capability)
        self.assertIsInstance(result, RetrievalProviderSelectionPolicyResult)
        self.assertEqual(result.status, "allowed")
        self.assertTrue(result.allowed)
        self.assertIsNone(result.reason)
        self.assertTrue(result.policy_evaluated)

    def test_unavailable_gate_returns_explicit_rejection(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.unavailable_result("maintenance")
        result = self.policy.evaluate("live_web", availability, self.health, self.capability)
        self.assertEqual(result.status, "rejected")
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "maintenance")

    def test_unhealthy_gate_returns_explicit_rejection(self):
        health = RetrievalProviderHealthEvaluationResult.unhealthy(
            type("Health", (), {"provider": "live_web", "reason": "timeout", "health_checked": True})()
        )
        result = self.policy.evaluate("live_web", self.availability, health, self.capability)
        self.assertEqual(result.reason, "timeout")

    def test_capability_gate_returns_explicit_rejection(self):
        capability = RetrievalProviderCapabilityEvaluationResult.unsupported_result(
            type("Request", (), {"source_type": "live_web", "temporal_scope": "historical"})()
        )
        result = self.policy.evaluate("live_web", self.availability, self.health, capability)
        self.assertEqual(result.reason, "retrieval_provider_capability_mismatch")

    def test_missing_capability_metadata_remains_allowed(self):
        result = self.policy.evaluate("live_web", self.availability, self.health, None)
        self.assertTrue(result.allowed)

    def test_result_serialization_is_deterministic(self):
        result = self.policy.evaluate("live_web", self.availability, self.health, self.capability)
        self.assertEqual(
            result.to_dict(),
            {
                "status": "allowed",
                "source_type": "live_web",
                "allowed": True,
                "reason": None,
                "policy_evaluated": True,
            },
        )

    def test_result_is_immutable(self):
        result = self.policy.evaluate("live_web", self.availability, self.health, self.capability)
        with self.assertRaises(AttributeError):
            result.allowed = False

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            self.policy.evaluate("", self.availability, self.health, self.capability)
        with self.assertRaises(ValueError):
            self.policy.evaluate("live_web", "available", self.health, self.capability)
        with self.assertRaises(ValueError):
            self.policy.evaluate("live_web", self.availability, "healthy", self.capability)
        with self.assertRaises(ValueError):
            self.policy.evaluate("live_web", self.availability, self.health, "supported")

    def test_result_rejects_inconsistent_state(self):
        with self.assertRaises(ValueError):
            RetrievalProviderSelectionPolicyResult(
                status="allowed", source_type="live_web", allowed=False
            )
        with self.assertRaises(ValueError):
            RetrievalProviderSelectionPolicyResult(
                status="rejected", source_type="live_web", allowed=True
            )


if __name__ == "__main__":
    unittest.main()
