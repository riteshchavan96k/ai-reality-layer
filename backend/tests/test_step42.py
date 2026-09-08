import unittest

from backend.app.orchestrator.orchestrator import orchestrate_task
from backend.app.reality.grounding_context import EvidenceGroundingContextBuilder
from backend.app.reality.grounded_result import GroundedResultEnvelopeBuilder
from backend.app.reality.retrieval_engine import RealityRetrievalEngine


class FakeRetrievalProvider:
    def retrieve(self, request: dict) -> dict:
        return {
            "status": "completed",
            "provider": "fake-provider",
            "sources": [
                {"title": "Example Source", "uri": "https://example.com/source"}
            ],
            "content": "Retrieved reality context.",
        }


class TestStep42GroundingIntegrity(unittest.TestCase):
    def setUp(self):
        self.builder = GroundedResultEnvelopeBuilder()
        self.context = EvidenceGroundingContextBuilder().build(
            "latest AI news",
            {
                "status": "usable",
                "content": "Fresh evidence",
                "sources": [{"title": "Example", "uri": "https://example.com"}],
            },
        )

    def test_ready_context_produces_grounded_result_envelope(self):
        envelope = self.builder.build(self.context, {"text": "answer"})
        self.assertEqual(envelope["status"], "ready")
        self.assertTrue(envelope["grounded"])
        self.assertEqual(envelope["source_count"], 1)

    def test_source_provenance_is_preserved(self):
        envelope = self.builder.build(self.context, {"text": "answer"})
        self.assertEqual(
            envelope["sources"],
            [{"title": "Example", "uri": "https://example.com"}],
        )

    def test_source_count_mismatch_is_rejected(self):
        invalid = {**self.context, "source_count": 2}
        with self.assertRaises(ValueError):
            self.builder.build(invalid, {"text": "answer"})

    def test_invalid_context_status_is_rejected(self):
        invalid = {**self.context, "status": "unknown"}
        with self.assertRaises(ValueError):
            self.builder.build(invalid, {"text": "answer"})

    def test_ready_context_requires_result(self):
        with self.assertRaises(ValueError):
            self.builder.build(self.context, None)

    def test_not_available_context_is_non_grounded(self):
        context = EvidenceGroundingContextBuilder().build(
            "current information",
            {"status": "insufficient", "content": None, "sources": []},
        )
        envelope = self.builder.build(context, None)
        self.assertEqual(envelope["status"], "not_available")
        self.assertFalse(envelope["grounded"])
        self.assertEqual(envelope["source_count"], 0)

    def test_orchestrator_exposes_stable_grounding_envelope(self):
        result = orchestrate_task(
            "latest AI news",
            retrieval_engine=RealityRetrievalEngine(FakeRetrievalProvider()),
        )
        self.assertEqual(result["grounding"]["status"], "ready")
        self.assertTrue(result["grounding"]["grounded"])
        self.assertEqual(result["grounding"]["source_count"], 1)


if __name__ == "__main__":
    unittest.main()
