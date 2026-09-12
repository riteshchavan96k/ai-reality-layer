import unittest

from backend.app.reality.retrieval_provider_health_contract import RetrievalProviderHealth


class Step76RetrievalProviderHealthTests(unittest.TestCase):
    def test_healthy_state(self):
        health = RetrievalProviderHealth.healthy("live_web")
        self.assertEqual(health.provider, "live_web")
        self.assertEqual(health.status, "healthy")
        self.assertTrue(health.is_healthy)
        self.assertTrue(health.health_checked)
        self.assertIsNone(health.reason)

    def test_unhealthy_state_preserves_reason(self):
        health = RetrievalProviderHealth.unhealthy("live_web", "timeout")
        self.assertEqual(health.status, "unhealthy")
        self.assertFalse(health.is_healthy)
        self.assertEqual(health.reason, "timeout")

    def test_unknown_state_is_not_healthy(self):
        health = RetrievalProviderHealth.unknown("live_web")
        self.assertEqual(health.status, "unknown")
        self.assertFalse(health.is_healthy)
        self.assertEqual(health.reason, "retrieval_provider_health_unknown")

    def test_serialization_is_stable(self):
        health = RetrievalProviderHealth.unhealthy("live_web", "maintenance")
        self.assertEqual(
            health.to_dict(),
            {
                "provider": "live_web",
                "status": "unhealthy",
                "reason": "maintenance",
                "health_checked": True,
            },
        )

    def test_contract_is_immutable(self):
        health = RetrievalProviderHealth.healthy("live_web")
        with self.assertRaises(Exception):
            health.status = "unhealthy"

    def test_invalid_provider_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderHealth.healthy("   ")

    def test_invalid_status_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderHealth("live_web", "degraded")

    def test_invalid_reason_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderHealth.unhealthy("live_web", "   ")

    def test_invalid_health_checked_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderHealth("live_web", "healthy", health_checked="yes")


if __name__ == "__main__":
    unittest.main()
