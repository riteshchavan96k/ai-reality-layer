import unittest

from backend.app.execution.execution_trace import ExecutionTrace
from backend.app.orchestrator.orchestrator import orchestrate_task


class TestStep27(unittest.TestCase):
    def test_trace_records_events(self):
        trace = ExecutionTrace()
        trace.record("analysis", "completed", task_type="general")

        events = trace.snapshot()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["stage"], "analysis")
        self.assertEqual(events[0]["status"], "completed")
        self.assertEqual(events[0]["task_type"], "general")
        self.assertIn("timestamp", events[0])

    def test_snapshot_returns_copy(self):
        trace = ExecutionTrace()
        trace.record("analysis", "completed")

        events = trace.snapshot()
        events[0]["status"] = "tampered"

        self.assertEqual(trace.snapshot()[0]["status"], "completed")

    def test_normal_orchestration_exposes_trace(self):
        result = orchestrate_task("Tell me about AI")

        self.assertEqual(result["status"], "orchestrated")
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
        self.assertEqual(result["trace"][-1]["status"], "not_improved")

    def test_human_approval_block_is_traced(self):
        result = orchestrate_task("Deploy this change to production")

        self.assertEqual(result["status"], "awaiting_human_approval")
        self.assertEqual(result["trace"][-1]["stage"], "execution")
        self.assertEqual(result["trace"][-1]["status"], "blocked")
        self.assertNotIn("result", result)

    def test_trace_contains_execution_metadata(self):
        result = orchestrate_task("Write Python code")

        execution_event = next(
            event for event in result["trace"] if event["stage"] == "execution"
        )

        self.assertEqual(execution_event["status"], "success")
        self.assertEqual(execution_event["model"], "mock-model")
        self.assertEqual(execution_event["attempts"], 1)
        self.assertFalse(execution_event["fallback_used"])


if __name__ == "__main__":
    unittest.main()
