import unittest
from unittest.mock import Mock

from backend.app.reality.retrieval_provider_availability_evaluation import RetrievalProviderAvailabilityEvaluationResult
from backend.app.reality.retrieval_provider_capability_evaluation import RetrievalProviderCapabilityEvaluationResult
from backend.app.reality.retrieval_provider_health_contract import RetrievalProviderHealth
from backend.app.reality.retrieval_provider_health_evaluation import RetrievalProviderHealthEvaluationResult
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_selection_policy import (
    DefaultRetrievalProviderSelectionPolicy,
    RetrievalProviderSelectionPolicy,
)
from backend.app.reality.retrieval_provider_selection_policy_result import RetrievalProviderSelectionPolicyResult
from backend.app.reality.retrieval_provider_selector import RegistryRetrievalProviderSelector


class StubProvider:
    provider_name = "live_web"

    def retrieve(self, request):
        return {"status": "completed", "sources": [], "content": "ok", "provider": self.provider_name}


class Step79RetrievalProviderSelectionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = DefaultRetrievalProviderSelectionPolicy()

    def test_policy_contract_is_satisfied(self):
        self.assertIsInstance(self.policy, RetrievalProviderSelectionPolicy)

    def test_all_supported_gates_allow_selection(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.available_result()
        health = RetrievalProviderHealthEvaluationResult.healthy(RetrievalProviderHealth.healthy("live_web"))
        capability = RetrievalProviderCapabilityEvaluationResult.supported_result(
            RetrievalProviderRequest(query="current status", source_type="live_web", temporal_scope="current")
        )
        result = self.policy.evaluate("live_web", availability, health, capability)
        self.assertTrue(result.allowed)

    def test_unavailable_gate_rejects_selection(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.unavailable_result("maintenance")
        health = RetrievalProviderHealthEvaluationResult.healthy(RetrievalProviderHealth.healthy("live_web"))
        result = self.policy.evaluate("live_web", availability, health, None)
        self.assertFalse(result.allowed)

    def test_unhealthy_gate_rejects_selection(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.available_result()
        health = RetrievalProviderHealthEvaluationResult.unhealthy(RetrievalProviderHealth.unhealthy("live_web", "timeout"))
        result = self.policy.evaluate("live_web", availability, health, None)
        self.assertFalse(result.allowed)

    def test_capability_mismatch_rejects_selection(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.available_result()
        health = RetrievalProviderHealthEvaluationResult.healthy(RetrievalProviderHealth.healthy("live_web"))
        capability = RetrievalProviderCapabilityEvaluationResult.unsupported_result(
            RetrievalProviderRequest(query="history", source_type="live_web", temporal_scope="historical")
        )
        result = self.policy.evaluate("live_web", availability, health, capability)
        self.assertFalse(result.allowed)

    def test_missing_capability_metadata_remains_backward_compatible(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.available_result()
        health = RetrievalProviderHealthEvaluationResult.healthy(RetrievalProviderHealth.healthy("live_web"))
        result = self.policy.evaluate("live_web", availability, health, None)
        self.assertTrue(result.allowed)

    def test_invalid_gate_inputs_are_rejected(self):
        availability = RetrievalProviderAvailabilityEvaluationResult.available_result()
        health = RetrievalProviderHealthEvaluationResult.healthy(RetrievalProviderHealth.healthy("live_web"))
        with self.assertRaises(ValueError):
            self.policy.evaluate("live_web", "available", health, None)
        with self.assertRaises(ValueError):
            self.policy.evaluate("live_web", availability, "healthy", None)
        with self.assertRaises(ValueError):
            self.policy.evaluate("live_web", availability, health, "supported")

    def test_selector_delegates_final_selection_decision_to_policy(self):
        registry = RetrievalProviderRegistry()
        registry.register("live_web", StubProvider())
        policy = Mock()
        policy.evaluate.return_value = RetrievalProviderSelectionPolicyResult.rejected_result("live_web", "custom_policy_rejected")
        selector = RegistryRetrievalProviderSelector(registry, selection_policy=policy)
        result = selector.select({"source_type": "live_web", "query": "current status"})
        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.reason, "custom_policy_rejected")
        policy.evaluate.assert_called_once()

    def test_selector_preserves_selection_when_policy_allows(self):
        registry = RetrievalProviderRegistry()
        provider = StubProvider()
        registry.register("live_web", provider)
        policy = Mock()
        policy.evaluate.return_value = RetrievalProviderSelectionPolicyResult.allowed_result("live_web")
        selector = RegistryRetrievalProviderSelector(registry, selection_policy=policy)
        result = selector.select({"source_type": "live_web", "query": "current status"})
        self.assertEqual(result.status, "selected")
        self.assertIs(result.provider, provider)
        policy.evaluate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
