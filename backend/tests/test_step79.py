import unittest

from backend.app.reality.retrieval_provider_availability_evaluation import RetrievalProviderAvailabilityEvaluationResult
from backend.app.reality.retrieval_provider_capability_evaluation import RetrievalProviderCapabilityEvaluationResult
from backend.app.reality.retrieval_provider_health_evaluation import RetrievalProviderHealthEvaluationResult
from backend.app.reality.retrieval_provider_selection_policy import (
    DefaultRetrievalProviderSelectionPolicy,
    RetrievalProviderSelectionPolicy,
)


class Step79RetrievalProviderSelectionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = DefaultRetrievalProviderSelectionPolicy()

    def test_policy_contract_is_satisfied(self):
        self.assertIsInstance(self.policy, RetrievalProviderSelectionPolicy)

    def test_all_supported_gates_allow_selection(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.available_result()
        health = RetrievalProviderHealthEvaluationResult.healthy(
            type("Health", (), {"provider": "live_web", "reason": None, "health_checked": True})()
        )
        capability = RetrievalProviderCapabilityEvaluationResult.supported_result(
            type("Request", (), {"source_type": "live_web", "temporal_scope": "current"})()
        )

        self.assertTrue(self.policy.allows(availability, health, capability))

    def test_unavailable_gate_rejects_selection(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.unavailable_result("maintenance")
        health = RetrievalProviderHealthEvaluationResult.healthy(
            type("Health", (), {"provider": "live_web", "reason": None, "health_checked": True})()
        )

        self.assertFalse(self.policy.allows(availability, health, None))

    def test_unhealthy_gate_rejects_selection(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.available_result()
        health = RetrievalProviderHealthEvaluationResult.unhealthy(
            type("Health", (), {"provider": "live_web", "reason": "timeout", "health_checked": True})()
        )

        self.assertFalse(self.policy.allows(availability, health, None))

    def test_capability_mismatch_rejects_selection(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.available_result()
        health = RetrievalProviderHealthEvaluationResult.healthy(
            type("Health", (), {"provider": "live_web", "reason": None, "health_checked": True})()
        )
        capability = RetrievalProviderCapabilityEvaluationResult.unsupported_result(
            type("Request", (), {"source_type": "live_web", "temporal_scope": "historical"})()
        )

        self.assertFalse(self.policy.allows(availability, health, capability))

    def test_missing_capability_metadata_remains_backward_compatible(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.available_result()
        health = RetrievalProviderHealthEvaluationResult.healthy(
            type("Health", (), {"provider": "live_web", "reason": None, "health_checked": True})()
        )

        self.assertTrue(self.policy.allows(availability, health, None))

    def test_invalid_gate_inputs_are_rejected(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.available_result()
        health = RetrievalProviderHealthEvaluationResult.healthy(
            type("Health", (), {"provider": "live_web", "reason": None, "health_checked": True})()
        )

        with self.assertRaises(ValueError):
            self.policy.allows("available", health, None)
        with self.assertRaises(ValueError):
            self.policy.allows(availability, "healthy", None)
        with self.assertRaises(ValueError):
            self.policy.allows(availability, health, "supported")


if __name__ == "__main__":
    unittest.main()
