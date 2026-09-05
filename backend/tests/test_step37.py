import unittest

from backend.app.reality.retrieval_contract import RealityRetrievalContract, RetrievalRequest


class TestStep37(unittest.TestCase):
    def setUp(self):
        self.contract = RealityRetrievalContract()

    def test_required_retrieval_request_is_ready(self):
        result = self.contract.build(
            "What is the latest AI news?",
            {
                "source_type": "live_web",
                "temporal_scope": "current",
                "requires_retrieval": True,
            },
        )
        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["request"]["required"])
        self.assertFalse(result["retrieval_executed"])

    def test_static_task_does_not_require_retrieval(self):
        result = self.contract.build(
            "Explain Python recursion",
            {
                "source_type": "model_knowledge",
                "temporal_scope": "unspecified",
                "requires_retrieval": False,
            },
        )
        self.assertEqual(result["status"], "not_required")
        self.assertFalse(result["request"]["required"])
        self.assertFalse(result["retrieval_executed"])

    def test_contract_preserves_query_and_temporal_scope(self):
        task = "What is the current price of a product?"
        result = self.contract.build(
            task,
            {
                "source_type": "live_web",
                "temporal_scope": "current",
                "requires_retrieval": True,
            },
        )
        self.assertEqual(result["request"]["query"], task)
        self.assertEqual(result["request"]["temporal_scope"], "current")

    def test_empty_query_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalRequest(query="", source_type="live_web")

    def test_empty_source_type_is_rejected(self):
        with self.assertRaises(ValueError):
            RetrievalRequest(query="latest AI news", source_type="")

    def test_empty_task_is_rejected(self):
        with self.assertRaises(ValueError):
            self.contract.build(
                "   ",
                {
                    "source_type": "live_web",
                    "requires_retrieval": True,
                },
            )


if __name__ == "__main__":
    unittest.main()
