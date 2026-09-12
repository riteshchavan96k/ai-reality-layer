import unittest

from backend.app.reality.retrieval_provider_capabilities import (
    RetrievalProviderCapabilities,
)
from backend.app.reality.retrieval_provider_request import RetrievalProviderRequest


class Step69RetrievalProviderCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.capabilities = RetrievalProviderCapabilities(
            source_types=("live_web", "documents"),
            temporal_scopes=("current", "historical", "unspecified"),
        )

    def test_capabilities_normalize_and_deduplicate_values(self):
        capabilities = RetrievalProviderCapabilities(
            source_types=(" Live_Web ", "live_web"),
            temporal_scopes=(" Current ", "current"),
        )

        self.assertEqual(capabilities.source_types, ("live_web",))
        self.assertEqual(capabilities.temporal_scopes, ("current",))

    def test_supports_matching_request(self):
        request = RetrievalProviderRequest(
            query="current reality",
            source_type="LIVE_WEB",
            temporal_scope="CURRENT",
        )

        self.assertTrue(self.capabilities.supports(request))

    def test_rejects_unsupported_source_type(self):
        request = RetrievalProviderRequest(
            query="current reality",
            source_type="database",
            temporal_scope="current",
        )

        self.assertFalse(self.capabilities.supports(request))

    def test_rejects_unsupported_temporal_scope(self):
        request = RetrievalProviderRequest(
            query="current reality",
            source_type="live_web",
            temporal_scope="forecast",
        )

        self.assertFalse(self.capabilities.supports(request))

    def test_rejects_invalid_capability_values(self):
        with self.assertRaises(ValueError):
            RetrievalProviderCapabilities(source_types=(), temporal_scopes=("current",))

        with self.assertRaises(ValueError):
            RetrievalProviderCapabilities(source_types=("live_web",), temporal_scopes=("",))

    def test_rejects_invalid_request_type(self):
        with self.assertRaises(ValueError):
            self.capabilities.supports({"source_type": "live_web"})

    def test_serializes_stably(self):
        self.assertEqual(
            self.capabilities.to_dict(),
            {
                "source_types": ["live_web", "documents"],
                "temporal_scopes": ["current", "historical", "unspecified"],
            },
        )


if __name__ == "__main__":
    unittest.main()
