import unittest

from backend.app.orchestrator.orchestrator import orchestrate_task
from backend.app.reality.source_planner import RealitySourcePlanner


class TestStep36(unittest.TestCase):
    def setUp(self):
        self.planner = RealitySourcePlanner()

    def test_current_information_requires_live_source(self):
        plan = self.planner.plan(
            {
                "needs_current_info": True,
                "needs_external_evidence": True,
                "temporal_scope": "current",
            }
        )
        self.assertEqual(plan["source_type"], "live_web")
        self.assertEqual(plan["priority"], "required")
        self.assertTrue(plan["requires_retrieval"])

    def test_external_evidence_requires_external_source(self):
        plan = self.planner.plan(
            {
                "needs_current_info": False,
                "needs_external_evidence": True,
                "temporal_scope": "unspecified",
            }
        )
        self.assertEqual(plan["source_type"], "web_or_official_source")
        self.assertTrue(plan["requires_retrieval"])

    def test_static_task_uses_model_knowledge(self):
        plan = self.planner.plan(
            {
                "needs_current_info": False,
                "needs_external_evidence": False,
                "temporal_scope": "unspecified",
            }
        )
        self.assertEqual(plan["source_type"], "model_knowledge")
        self.assertEqual(plan["priority"], "optional")
        self.assertFalse(plan["requires_retrieval"])

    def test_current_information_has_priority_over_generic_evidence(self):
        plan = self.planner.plan(
            {
                "needs_current_info": True,
                "needs_external_evidence": True,
                "temporal_scope": "current",
            }
        )
        self.assertEqual(plan["source_type"], "live_web")

    def test_plan_preserves_temporal_scope(self):
        plan = self.planner.plan(
            {
                "needs_current_info": True,
                "needs_external_evidence": True,
                "temporal_scope": "current",
            }
        )
        self.assertEqual(plan["temporal_scope"], "current")

    def test_orchestrator_exposes_source_plan(self):
        result = orchestrate_task("What is the latest news about AI?", human_approved=True)
        self.assertEqual(
            result["analysis"]["reality_context"]["status"],
            "required",
        )
        self.assertEqual(
            result["analysis"]["reality_source_plan"]["source_type"],
            "live_web",
        )
        self.assertTrue(result["analysis"]["reality_source_plan"]["requires_retrieval"])


if __name__ == "__main__":
    unittest.main()
