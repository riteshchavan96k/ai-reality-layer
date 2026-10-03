import unittest

from backend.app.orchestrator.orchestrator import orchestrate_task
from backend.app.reality.context_requirements import RealityContextRequirementDetector


class TestStep35(unittest.TestCase):
    def setUp(self):
        self.detector = RealityContextRequirementDetector()

    def test_current_task_requires_external_evidence(self):
        result = self.detector.detect("What is the latest AI news?")

        self.assertTrue(result["needs_current_info"])
        self.assertTrue(result["needs_external_evidence"])
        self.assertEqual(result["temporal_scope"], "current")
        self.assertEqual(result["status"], "required")
        self.assertIn("latest", result["current_signals"])
        self.assertIn("news", result["evidence_signals"])

    def test_explicit_source_request_requires_external_evidence(self):
        result = self.detector.detect("Explain Python recursion with sources")

        self.assertFalse(result["needs_current_info"])
        self.assertTrue(result["needs_external_evidence"])
        self.assertEqual(result["temporal_scope"], "unspecified")
        self.assertEqual(result["status"], "required")
        self.assertIn("sources", result["evidence_signals"])

    def test_static_task_does_not_require_reality_context(self):
        result = self.detector.detect("Explain Python recursion")

        self.assertFalse(result["needs_current_info"])
        self.assertFalse(result["needs_external_evidence"])
        self.assertEqual(result["temporal_scope"], "unspecified")
        self.assertEqual(result["status"], "not_required")

    def test_detection_is_case_insensitive(self):
        result = self.detector.detect("LATEST WEATHER Today")

        self.assertTrue(result["needs_current_info"])
        self.assertTrue(result["needs_external_evidence"])
        self.assertIn("latest", result["current_signals"])
        self.assertIn("weather", result["evidence_signals"])

    def test_signals_match_words_not_substrings(self):
        result = self.detector.detect("Explain how to deliver a programming solution")

        self.assertFalse(result["needs_current_info"])
        self.assertFalse(result["needs_external_evidence"])
        self.assertEqual(result["current_signals"], [])
        self.assertEqual(result["evidence_signals"], [])

    def test_orchestrator_exposes_reality_context(self):
        result = orchestrate_task("What is the latest AI news?")

        context = result["analysis"]["reality_context"]

        self.assertTrue(context["needs_current_info"])
        self.assertTrue(context["needs_external_evidence"])
        self.assertEqual(context["temporal_scope"], "current")
        self.assertEqual(result["trace"][0]["stage"], "analysis")
        self.assertTrue(result["trace"][0]["needs_current_info"])
        self.assertTrue(result["trace"][0]["needs_external_evidence"])

    def test_static_orchestration_preserves_existing_flow(self):
        result = orchestrate_task("Explain Python recursion")

        self.assertEqual(result["status"], "orchestrated")
        self.assertFalse(result["analysis"]["reality_context"]["needs_external_evidence"])
        stages = [event["stage"] for event in result["trace"]]
        core_stages = [
            "analysis",
            "routing",
            "approval",
            "execution",
            "evaluation",
            "quality_recovery",
        ]
        self.assertEqual(
            [stage for stage in stages if stage in core_stages],
            core_stages,
        )


if __name__ == "__main__":
    unittest.main()
