import unittest

from backend.app.reality.retrieval_engine import RealityRetrievalEngine


class Provider:
    name = "test-provider"

    def __init__(self, result=None, error=False):
        self.result = result
        self.error = error
        self.calls = []

    def retrieve(self, request):
        self.calls.append(request.to_dict())
        if self.error:
            raise RuntimeError("provider failure")
        return self.result


class TestStep55(unittest.TestCase):
    def _contract(self, required=True):
        return {
            "status": "ready" if required else "not_required",
            "request": {
                "query": "latest AI news",
                "source_type": "live_web",
                "temporal_scope": "current",
                "required": required,
            },
            "retrieval_executed": False,
        }

    def test_completed_provider_output_uses_stable_result_contract(self):
        provider = Provider(
            {
                "status": "completed",
                "provider": "web-provider",
                "sources": [{"title": "AI News", "uri": "https://example.test/ai"}],
                "content": "current evidence",
            }
        )

        result = RealityRetrievalEngine(provider).retrieve(self._contract())

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["provider"], "web-provider")
        self.assertTrue(result["retrieval_executed"])
        self.assertEqual(result["content"], "current evidence")
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(len(provider.calls), 1)

    def test_provider_unavailable_is_blocked_without_claiming_execution(self):
        provider = Provider({"status": "provider_unavailable"})

        result = RealityRetrievalEngine(provider).retrieve(self._contract())

        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["retrieval_executed"])
        self.assertEqual(result["sources"], [])
        self.assertIsNone(result["content"])

    def test_provider_failure_is_stable_and_does_not_expose_exception(self):
        provider = Provider(error=True)

        result = RealityRetrievalEngine(provider).retrieve(self._contract())

        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["retrieval_executed"])
        self.assertEqual(result["reason"], "retrieval_provider_failed")
        self.assertNotIn("provider failure", str(result))
        self.assertEqual(result["sources"], [])
        self.assertIsNone(result["content"])

    def test_invalid_provider_output_is_converted_to_stable_failure(self):
        provider = Provider({"status": "completed", "sources": "invalid"})

        result = RealityRetrievalEngine(provider).retrieve(self._contract())

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "retrieval_provider_failed")

    def test_not_required_retrieval_does_not_execute_provider(self):
        provider = Provider({"status": "completed", "content": "should not run"})

        result = RealityRetrievalEngine(provider).retrieve(self._contract(required=False))

        self.assertEqual(result["status"], "not_required")
        self.assertFalse(result["retrieval_executed"])
        self.assertEqual(provider.calls, [])


if __name__ == "__main__":
    unittest.main()
