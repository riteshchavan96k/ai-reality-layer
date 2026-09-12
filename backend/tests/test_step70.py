import unittest

from backend.app.reality.retrieval_provider_capabilities import RetrievalProviderCapabilities
from backend.app.reality.retrieval_provider_descriptor import RetrievalProviderDescriptor
from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest
from backend.app.reality.retrieval_provider_selection import RetrievalProviderSelectionResult
from backend.app.reality.retrieval_provider_selector import RegistryRetrievalProviderSelector


class Provider:
    name = "capable_provider"


class Step70CapabilityAwareSelectionTests(unittest.TestCase):
    def setUp(self):
        self.provider = Provider()
        self.registry = RetrievalProviderRegistry()
        self.selector = RegistryRetrievalProviderSelector(self.registry)
        self.descriptor = RetrievalProviderDescriptor(
            name="capable_provider",
            capabilities=RetrievalProviderCapabilities(
                source_types=("live_web",),
                temporal_scopes=("current",),
            ),
            provider=self.provider,
        )

    def test_descriptor_exposes_stable_capability_metadata(self):
        self.assertTrue(
            self.descriptor.supports(
                RetrievalProviderRequest(
                    query="current reality",
                    source_type="live_web",
                    temporal_scope="current",
                )
            )
        )
        self.assertEqual(
            self.descriptor.to_dict(),
            {
                "name": "capable_provider",
                "capabilities": {
                    "source_types": ["live_web"],
                    "temporal_scopes": ["current"],
                },
            },
        )

    def test_registry_stores_descriptor_and_provider_together(self):
        self.registry.register_descriptor("live_web", self.descriptor)
        self.assertIs(self.registry.get("live_web"), self.provider)
        self.assertIs(self.registry.get_descriptor("live_web"), self.descriptor)

    def test_selector_accepts_capability_compatible_request(self):
        self.registry.register_descriptor("live_web", self.descriptor)

        result = self.selector.select(
            {
                "query": "current reality",
                "source_type": "live_web",
                "temporal_scope": "current",
                "required": True,
            }
        )

        self.assertEqual(result.status, "selected")
        self.assertIs(result.provider, self.provider)

    def test_selector_blocks_capability_mismatch(self):
        self.registry.register_descriptor("live_web", self.descriptor)

        result = self.selector.select(
            {
                "query": "old reality",
                "source_type": "live_web",
                "temporal_scope": "historical",
                "required": True,
            }
        )

        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.reason, "retrieval_provider_capability_mismatch")
        self.assertFalse(result.selection_executed)

    def test_legacy_provider_registration_preserves_selection(self):
        self.registry.register("live_web", self.provider)
        result = self.selector.select(
            {
                "query": "current reality",
                "source_type": "live_web",
                "temporal_scope": "current",
                "required": True,
            }
        )
        self.assertEqual(result.status, "selected")
        self.assertIs(result.provider, self.provider)

    def test_descriptor_rejects_empty_name(self):
        with self.assertRaises(ValueError):
            RetrievalProviderDescriptor(
                name="",
                capabilities=self.descriptor.capabilities,
                provider=self.provider,
            )


if __name__ == "__main__":
    unittest.main()
