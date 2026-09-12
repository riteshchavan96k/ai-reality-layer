import unittest

from backend.app.reality.retrieval_provider_availability import RetrievalProviderAvailability
from backend.app.reality.retrieval_provider_capabilities import RetrievalProviderCapabilities
from backend.app.reality.retrieval_provider_descriptor import RetrievalProviderDescriptor
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_selector import RegistryRetrievalProviderSelector


class StubProvider:
    def retrieve(self, request):
        return {"status": "completed", "provider": "stub", "sources": [], "content": ""}


class Step73RetrievalProviderAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.provider = StubProvider()
        self.registry = RetrievalProviderRegistry()
        self.registry.register("live_web", self.provider)
        self.selector = RegistryRetrievalProviderSelector(self.registry)

    def test_available_state_is_stable_and_serializable(self):
        availability = RetrievalProviderAvailability.available()
        self.assertTrue(availability.is_available)
        self.assertEqual(availability.to_dict()["status"], "available")
        self.assertTrue(availability.to_dict()["availability_checked"])

    def test_unavailable_state_preserves_reason(self):
        availability = RetrievalProviderAvailability.unavailable("provider_maintenance")
        self.assertFalse(availability.is_available)
        self.assertEqual(availability.reason, "provider_maintenance")

    def test_blocked_state_is_not_available(self):
        availability = RetrievalProviderAvailability.blocked("provider_policy_blocked")
        self.assertFalse(availability.is_available)
        self.assertEqual(availability.status, "blocked")

    def test_invalid_availability_state_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderAvailability("unknown")

    def test_registry_accepts_explicit_availability(self):
        availability = RetrievalProviderAvailability.unavailable("maintenance")
        self.registry.register_availability("live_web", availability)
        self.assertEqual(self.registry.get_availability("live_web"), availability)

    def test_selector_does_not_select_unavailable_provider(self):
        self.registry.register_availability("live_web", RetrievalProviderAvailability.unavailable("maintenance"))
        result = self.selector.select({"source_type": "live_web", "query": "current reality"})
        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.reason, "maintenance")
        self.assertIsNone(result.provider)

    def test_selector_does_not_select_blocked_provider(self):
        self.registry.register_availability("live_web", RetrievalProviderAvailability.blocked("policy_blocked"))
        result = self.selector.select({"source_type": "live_web", "query": "current reality"})
        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.reason, "policy_blocked")

    def test_provider_without_explicit_availability_remains_compatible(self):
        result = self.selector.select({"source_type": "live_web", "query": "current reality"})
        self.assertEqual(result.status, "selected")
        self.assertIs(result.provider, self.provider)

    def test_descriptor_capability_check_still_runs_after_availability(self):
        capabilities = RetrievalProviderCapabilities(
            source_types=("live_web",),
            temporal_scopes=("historical",),
        )
        self.registry.register_descriptor(
            "live_web",
            RetrievalProviderDescriptor("stub", capabilities, self.provider),
        )
        result = self.selector.select({
            "source_type": "live_web",
            "temporal_scope": "current",
            "query": "current reality",
        })
        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.reason, "retrieval_provider_capability_mismatch")


if __name__ == "__main__":
    unittest.main()
