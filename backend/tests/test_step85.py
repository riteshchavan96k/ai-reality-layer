import unittest

from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.retrieval_result_consumer import RetrievalResultConsumer
from backend.app.reality.retrieval_result import RetrievalResultContract
from backend.app.reality.retrieval_result_consumption import RetrievalResultConsumption


class TestRetrievalResultConsumption(unittest.TestCase):
    def setUp(self):
        self.consumer = RetrievalResultConsumer()
        self.request = {
            "query": "test query",
            "source_type": "live_web",
            "temporal_scope": "current",
            "required": True,
        }

    def test_completed_result_with_content_is_usable(self):
        result = self.consumer.consume(
            RetrievalResultContract.completed(
                self.request, "test-provider", [], "current facts"
            )
        )
        self.assertEqual(result.status, "usable")
        self.assertTrue(result.usable)
        self.assertEqual(result.retrieval_status, "completed")

    def test_completed_result_with_sources_is_usable(self):
        result = self.consumer.consume(
            RetrievalResultContract.completed(
                self.request,
                "test-provider",
                [{"title": "Example"}],
                None,
            )
        )
        self.assertTrue(result.usable)

    def test_empty_completed_result_is_rejected(self):
        result = self.consumer.consume(
            RetrievalResultContract.completed(
                self.request, "test-provider", [], None
            )
        )
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.reason, "empty_retrieval_result")

    def test_failed_result_is_rejected(self):
        result = self.consumer.consume(
            RetrievalResultContract.failed(
                self.request, "test-provider", "provider_error"
            )
        )
        self.assertFalse(result.usable)
        self.assertEqual(result.reason, "provider_error")

    def test_blocked_result_is_rejected(self):
        result = self.consumer.consume(
            RetrievalResultContract.blocked(
                self.request, None, "provider_unavailable"
            )
        )
        self.assertEqual(result.reason, "provider_unavailable")

    def test_not_required_is_usable_without_evidence(self):
        request = {**self.request, "required": False}
        result = self.consumer.consume(
            RetrievalResultContract.not_required(request)
        )
        self.assertTrue(result.usable)
        self.assertEqual(result.retrieval_status, "not_required")

    def test_invalid_sources_are_rejected_by_canonical_boundary(self):
        malformed = {
            "status": "completed",
            "provider": "test-provider",
            "request": self.request,
            "sources": "invalid",
            "content": "x",
            "retrieval_executed": True,
        }
        with self.assertRaises(ValueError):
            self.consumer.consume(malformed)

    def test_invalid_content_is_rejected_by_canonical_boundary(self):
        malformed = {
            "status": "completed",
            "provider": "test-provider",
            "request": self.request,
            "sources": [],
            "content": 123,
            "retrieval_executed": True,
        }
        with self.assertRaises(ValueError):
            self.consumer.consume(malformed)

    def test_unsupported_status_is_rejected_by_canonical_boundary(self):
        malformed = {
            "status": "unknown",
            "provider": None,
            "request": self.request,
            "sources": [],
            "content": None,
            "retrieval_executed": False,
        }
        with self.assertRaises(ValueError):
            self.consumer.consume(malformed)

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(ValueError):
            self.consumer.consume("invalid")

    def test_consumption_contract_is_immutable(self):
        result = RetrievalResultConsumption.usable_result()
        with self.assertRaises(Exception):
            result.usable = False

    def test_default_dependencies_include_consumer(self):
        dependencies = OrchestrationDependencies.default()
        self.assertIsInstance(
            dependencies.retrieval_result_consumer,
            RetrievalResultConsumer,
        )


if __name__ == "__main__":
    unittest.main()
