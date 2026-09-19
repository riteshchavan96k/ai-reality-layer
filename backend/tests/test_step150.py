import unittest

from backend.app.reality.retrieval_result import RetrievalResultContract
from backend.app.reality.retrieval_result_consumer import RetrievalResultConsumer


class Step150RetrievalResultConsumptionValidationTests(unittest.TestCase):
    def setUp(self):
        self.request = {"query": "current fact", "source_type": "live_web", "required": True}

    def test_validate_accepts_canonical_completed_result(self):
        result = RetrievalResultContract.completed(
            self.request, "http_retrieval",
            [{"uri": "https://example.test"}], "fact"
        )
        self.assertEqual(RetrievalResultContract.validate(result), result)

    def test_consumer_rejects_missing_required_result_field(self):
        result = RetrievalResultContract.completed(
            self.request, "http_retrieval",
            [{"uri": "https://example.test"}], "fact"
        )
        result.pop("retrieval_executed")
        with self.assertRaisesRegex(ValueError, "missing required fields"):
            RetrievalResultConsumer().consume(result)

    def test_consumer_rejects_status_execution_inconsistency(self):
        result = RetrievalResultContract.completed(
            self.request, "http_retrieval",
            [{"uri": "https://example.test"}], "fact"
        )
        result["retrieval_executed"] = False
        with self.assertRaisesRegex(ValueError, "retrieval_executed is inconsistent"):
            RetrievalResultConsumer().consume(result)

    def test_consumer_rejects_failed_result_with_payload(self):
        result = RetrievalResultContract.failed(
            self.request, "http_retrieval", "upstream_failed"
        )
        result["content"] = "unexpected"
        with self.assertRaisesRegex(ValueError, "non-completed results must not contain content"):
            RetrievalResultConsumer().consume(result)

    def test_consumer_accepts_canonical_not_required_result(self):
        result = RetrievalResultContract.not_required(self.request)
        decision = RetrievalResultConsumer().consume(result)
        self.assertEqual(decision.status, "usable")
        self.assertEqual(decision.retrieval_status, "not_required")


if __name__ == "__main__":
    unittest.main()
