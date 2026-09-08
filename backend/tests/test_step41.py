import unittest

from backend.app.orchestrator.orchestrator import orchestrate_task
from backend.app.reality.grounding_context import EvidenceGroundingContextBuilder
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


class TestStep41EvidenceGrounding(unittest.TestCase):
    def setUp(self):
        self.builder = EvidenceGroundingContextBuilder()

    def test_usable_evidence_becomes_ready_grounding_context(self):
        context = self.builder.build(
            "latest AI news",
            {
                "status": "usable",
                "content": "Fresh evidence",
                "sources": [{"title": "Example", "uri": "https://example.com"}],
            },
        )
        self.assertEqual(context["status"], "ready")
        self.assertEqual(context["content"], "Fresh evidence")
        self.assertEqual(context["source_count"], 1)

    def test_source_provenance_is_preserved(self):
        context = self.builder.build(
            "current information",
            {
                "status": "usable",
                "content": "Evidence",
                "sources": [{"title": "Official source", "uri": "https://example.com/a"}],
            },
        )
        self.assertEqual(
            context["sources"],
            [{"title": "Official source", "uri": "https://example.com/a"}],
        )

    def test_unusable_evidence_does_not_become_model_context(self):
        context = self.builder.build(
            "current information",
            {"status": "insufficient", "content": None, "sources": []},
        )
        self.assertEqual(context["status"], "not_available")
        self.assertIsNone(context["content"])
        self.assertEqual(context["source_count"], 0)

    def test_invalid_task_is_rejected(self):
        with self.assertRaises(ValueError):
            self.builder.build("", {"status": "usable", "content": "x", "sources": []})

    def test_invalid_evidence_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            self.builder.build("task", [])

    def test_invalid_source_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            self.builder.build(
                "task",
                {"status": "usable", "content": "x", "sources": ["bad"]},
            )

    def test_invalid_content_type_is_rejected(self):
        with self.assertRaises(ValueError):
            self.builder.build(
                "task",
                {"status": "usable", "content": 123, "sources": []},
            )

    def test_orchestrator_injects_grounding_context_into_model_execution(self):
        result = orchestrate_task(
            "latest AI news",
            retrieval_engine=RealityRetrievalEngine(FakeRetrievalProvider()),
        )

        grounding = result["analysis"]["reality_retrieval"]["grounding"]
        self.assertEqual(grounding["status"], "ready")
        self.assertEqual(grounding["source_count"], 1)
        self.assertEqual(result["result"]["grounding"]["status"], "ready")
        self.assertTrue(result["result"]["grounding"]["grounded"])

    def test_required_retrieval_never_reaches_model_without_usable_grounding(self):
        result = orchestrate_task("latest AI news")

        self.assertEqual(result["status"], "retrieval_unavailable")
        self.assertEqual(
            result["analysis"]["reality_retrieval"]["grounding"]["status"],
            "not_available",
        )


if __name__ == "__main__":
    unittest.main()
