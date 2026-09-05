import unittest

from backend.app.reality.retrieval_engine import RealityRetrievalEngine


class FakeRetrievalProvider:
    def retrieve(self, request: dict) -> dict:
        return {
            "status": "completed",
            "provider": "fake-provider",
            "sources": [
                {
                    "title": "Example Source",
                    "uri": "https://example.com/source",
                }
            ],
            "content": "Retrieved reality context.",
        }


class TestStep38(unittest.TestCase):
    def test_required_contract_executes_provider(self):
        contract = {
            "status": "ready",
            "request": {
                "query": "latest AI news",
                "source_type": "live_web",
                "temporal_scope": "current",
                "required": True,
            },
        }

        result = RealityRetrievalEngine(FakeRetrievalProvider()).retrieve(contract)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["provider"], "fake-provider")
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(result["content"], "Retrieved reality context.")

    def test_static_contract_skips_provider(self):
        contract = {
            "status": "not_required",
            "request": {
                "query": "explain Python variables",
                "source_type": "model_knowledge",
                "temporal_scope": "unspecified",
                "required": False,
            },
        }

        result = RealityRetrievalEngine(FakeRetrievalProvider()).retrieve(contract)

        self.assertEqual(result["status"], "not_required")
        self.assertIsNone(result["provider"])
        self.assertEqual(result["sources"], [])
        self.assertIsNone(result["content"])

    def test_missing_provider_is_explicit(self):
        contract = {
            "status": "ready",
            "request": {
                "query": "latest AI news",
                "source_type": "live_web",
                "temporal_scope": "current",
                "required": True,
            },
        }

        result = RealityRetrievalEngine().retrieve(contract)

        self.assertEqual(result["status"], "provider_unavailable")
        self.assertIsNone(result["provider"])
        self.assertEqual(result["sources"], [])

    def test_provider_output_is_normalized(self):
        class MinimalProvider:
            def retrieve(self, request):
                return {"status": "completed", "content": "context"}

        contract = {
            "status": "ready",
            "request": {
                "query": "today weather",
                "source_type": "live_web",
                "temporal_scope": "current",
                "required": True,
            },
        }

        result = RealityRetrievalEngine(MinimalProvider()).retrieve(contract)

        self.assertEqual(result["status"], "completed")
        self.assertIsNone(result["provider"])
        self.assertEqual(result["sources"], [])
        self.assertEqual(result["content"], "context")

    def test_invalid_contract_is_rejected(self):
        with self.assertRaises(ValueError):
            RealityRetrievalEngine().retrieve(None)

    def test_missing_request_for_required_contract_is_rejected(self):
        with self.assertRaises(ValueError):
            RealityRetrievalEngine().retrieve({"status": "ready"})


if __name__ == "__main__":
    unittest.main()
