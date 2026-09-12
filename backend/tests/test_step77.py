import unittest

from backend.app.reality.retrieval_provider_health import RetrievalProviderHealth


class Step77RetrievalProviderHealthTests(unittest.TestCase):
    def test_healthy_state(self):
        health = RetrievalProviderHealth.healthy()
        self.assertEqual(health.status, "healthy")
        self.assertTrue(health.is_healthy)
        self.assertTrue(health.health_checked)
        self.assertIsNone(health.reason)

    def test_unhealthy_state_preserves_reason(self):
        health = RetrievalProviderHealth.unhealthy("timeout")
        self.assertEqual(health.status, "unhealthy")
        self.assertFalse(health.is_healthy)
        self.assertEqual(health.reason, "timeout")

    def test_unknown_state_is_not_healthy(self):
        health = RetrievalProviderHealth.unknown()
        self.assertEqual(health.status, "unknown")
        self.assertFalse(health.is_healthy)
        self.assertEqual(health.reason, "retrieval_provider_health_unknown")

    def test_serialization_is_stable(self):
        health = RetrievalProviderHealth.unhealthy("maintenance")
        self.assertEqual(
            health.to_dict(),
            {
                "status": "unhealthy",
                "reason": "maintenance",
                "health_checked": True,
            },
        )

    def test_contract_is_immutable(self):
        health = RetrievalProviderHealth.healthy()
        with self.assertRaises(Exception):
            health.status = "unhealthy"

    def test_invalid_status_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderHealth("degraded")

    def test_invalid_reason_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderHealth.unhealthy("   ")

    def test_invalid_health_checked_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalProviderHealth("healthy", health_checked="yes")


if __name__ == "__main__":
    unittest.main()
