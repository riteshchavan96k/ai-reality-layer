import unittest

from backend.app.reality.retrieval_result import RetrievalResultContract
from backend.app.reality.retrieval_engine import RealityRetrievalEngine


class Step148NotRequiredRetrievalResultTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            "query": "stable fact",
            "source_type": "model_knowledge",
            "temporal_scope": "unspecified",
            "required": False,
        }

    def test_not_required_result_has_canonical_shape(self):
        result = RetrievalResultContract.not_required(self.request)

        self.assertEqual(result["status"], "not_required")
        self.assertIsNone(result["provider"])
        self.assertEqual(result["request"], self.request)
        self.assertEqual(result["sources"], [])
        self.assertIsNone(result["content"])
        self.assertFalse(result["retrieval_executed"])
        self.assertNotIn("reason", result)

    def test_not_required_result_rejects_provider(self):
        with self.assertRaisesRegex(ValueError, "not_required results must not contain a provider"):
            RetrievalResultContract.validate({
                "status": "not_required",
                "request": self.request,
                "provider": "http_retrieval",
                "sources": [],
                "content": None,
                "retrieval_executed": False,
            })

    def test_not_required_result_rejects_payload(self):
        with self.assertRaises(ValueError):
            RetrievalResultContract.validate({
                "status": "not_required",
                "request": self.request,
                "provider": None,
                "sources": [{"uri": "https://example.test/source"}],
                "content": None,
                "retrieval_executed": False,
            })

        with self.assertRaises(ValueError):
            RetrievalResultContract.validate({
                "status": "not_required",
                "request": self.request,
                "provider": None,
                "sources": [],
                "content": "unexpected",
                "retrieval_executed": False,
            })

    def test_not_required_result_rejects_reason_and_execution_claim(self):
        with self.assertRaises(ValueError):
            RetrievalResultContract.validate({
                "status": "not_required",
                "request": self.request,
                "provider": None,
                "sources": [],
                "content": None,
                "reason": "unexpected",
                "retrieval_executed": False,
            })

        with self.assertRaisesRegex(ValueError, "retrieval_executed is inconsistent"):
            RetrievalResultContract.validate({
                "status": "not_required",
                "request": self.request,
                "provider": None,
                "sources": [],
                "content": None,
                "retrieval_executed": True,
            })

    def test_engine_uses_canonical_not_required_result(self):
        engine = RealityRetrievalEngine()
        result = engine.retrieve({
            "status": "not_required",
            "request": self.request,
        })

        self.assertEqual(result, RetrievalResultContract.not_required(self.request))

    def test_engine_rejects_missing_not_required_request(self):
        engine = RealityRetrievalEngine()

        with self.assertRaisesRegex(
            ValueError,
            "retrieval contract request must be a dictionary",
        ):
            engine.retrieve({"status": "not_required", "request": None})


if __name__ == "__main__":
    unittest.main()
