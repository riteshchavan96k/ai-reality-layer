import unittest

from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.retrieval_result_consumer import RetrievalResultConsumer
from backend.app.reality.retrieval_result_consumption import RetrievalResultConsumption


class TestRetrievalResultConsumption(unittest.TestCase):
    def setUp(self):
        self.consumer = RetrievalResultConsumer()

    def test_completed_result_with_content_is_usable(self):
        result = self.consumer.consume(
            {"status": "completed", "sources": [], "content": "current facts"}
        )
        self.assertEqual(result.status, "usable")
        self.assertTrue(result.usable)
        self.assertEqual(result.retrieval_status, "completed")

    def test_completed_result_with_sources_is_usable(self):
        result = self.consumer.consume(
            {"status": "completed", "sources": [{"title": "Example"}], "content": None}
        )
        self.assertTrue(result.usable)

    def test_empty_completed_result_is_rejected(self):
        result = self.consumer.consume(
            {"status": "completed", "sources": [], "content": None}
        )
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.reason, "empty_retrieval_result")

    def test_failed_result_is_rejected(self):
        result = self.consumer.consume(
            {"status": "failed", "reason": "provider_error"}
        )
        self.assertFalse(result.usable)
        self.assertEqual(result.reason, "provider_error")

    def test_blocked_result_is_rejected(self):
        result = self.consumer.consume(
            {"status": "blocked", "reason": "provider_unavailable"}
        )
        self.assertEqual(result.reason, "provider_unavailable")

    def test_not_required_is_usable_without_evidence(self):
        result = self.consumer.consume({"status": "not_required"})
        self.assertTrue(result.usable)
        self.assertEqual(result.retrieval_status, "not_required")

    def test_invalid_sources_are_rejected(self):
        result = self.consumer.consume(
            {"status": "completed", "sources": "invalid", "content": "x"}
        )
        self.assertEqual(result.reason, "invalid_retrieval_sources")

    def test_invalid_content_is_rejected(self):
        result = self.consumer.consume(
            {"status": "completed", "sources": [], "content": 123}
        )
        self.assertEqual(result.reason, "invalid_retrieval_content")

    def test_unsupported_status_is_rejected(self):
        result = self.consumer.consume({"status": "unknown"})
        self.assertFalse(result.usable)
        self.assertEqual(result.reason, "unsupported_retrieval_status")

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(ValueError):
            self.consumer.consume("invalid")

    def test_consumption_contract_is_immutable(self):
        result = RetrievalResultConsumption.usable_result()
        with self.assertRaises(Exception):
            result.usable = False

    def test_default_dependencies_include_consumer(self):
        dependencies = OrchestrationDependencies.default()
        self.assertIsInstance(dependencies.retrieval_result_consumer, RetrievalResultConsumer)


if __name__ == "__main__":
    unittest.main()
