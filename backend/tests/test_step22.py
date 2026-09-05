import unittest

from backend.app.controls.human_in_the_loop import HumanApprovalPolicy
from backend.app.orchestrator.orchestrator import orchestrate_task


class TestStep22(unittest.TestCase):
    def test_normal_task_does_not_require_approval(self):
        result = orchestrate_task("Tell me about AI")
        self.assertEqual(result["status"], "orchestrated")
        self.assertFalse(result["approval"]["required"])

    def test_risk_task_requires_approval_before_execution(self):
        result = orchestrate_task("Deploy this change to production")
        self.assertEqual(result["status"], "awaiting_human_approval")
        self.assertTrue(result["approval"]["required"])
        self.assertIn("deploy", result["approval"]["matched_keywords"])
        self.assertNotIn("result", result)

    def test_approved_risk_task_can_execute(self):
        result = orchestrate_task("Deploy this change to production", human_approved=True)
        self.assertEqual(result["status"], "orchestrated")
        self.assertTrue(result["approval"]["required"])
        self.assertIn("result", result)

    def test_always_policy_requires_approval(self):
        policy = HumanApprovalPolicy(mode="always")
        result = orchestrate_task("Tell me about AI", approval_policy=policy)
        self.assertEqual(result["status"], "awaiting_human_approval")
        self.assertTrue(result["approval"]["required"])

    def test_never_policy_disables_approval(self):
        policy = HumanApprovalPolicy(mode="never")
        result = orchestrate_task("Deploy this change to production", approval_policy=policy)
        self.assertEqual(result["status"], "orchestrated")
        self.assertFalse(result["approval"]["required"])

    def test_invalid_policy_mode_is_rejected(self):
        policy = HumanApprovalPolicy(mode="invalid")
        with self.assertRaises(ValueError):
            policy.evaluate("Tell me about AI", {"confidence": 0.5}, {})


if __name__ == "__main__":
    unittest.main()
