import unittest

from backend.app.execution.retry_policy import RetryPolicy
from backend.app.orchestrator.orchestrator import orchestrate_task


class TestStep25(unittest.TestCase):
    def test_successful_operation_runs_once(self):
        calls = []

        def operation():
            calls.append(1)
            return {"text": "ok"}

        result = RetryPolicy(max_attempts=3).execute(operation)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(len(calls), 1)

    def test_transient_failure_is_retried(self):
        calls = []

        def operation():
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError("temporary failure")
            return {"text": "recovered"}

        result = RetryPolicy(max_attempts=2).execute(operation)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(len(calls), 2)

    def test_exhausted_retries_return_safe_failure(self):
        calls = []

        def operation():
            calls.append(1)
            raise RuntimeError("internal detail")

        result = RetryPolicy(max_attempts=2).execute(operation)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["error"], "internal detail")
        self.assertEqual(len(calls), 2)

    def test_invalid_retry_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            RetryPolicy(max_attempts=0)

    def test_orchestrator_reports_execution_metadata(self):
        result = orchestrate_task("Tell me about AI")
        self.assertEqual(result["status"], "orchestrated")
        self.assertEqual(result["execution"]["status"], "success")
        self.assertEqual(result["execution"]["attempts"], 1)

    def test_human_approval_still_blocks_execution(self):
        result = orchestrate_task("Deploy this change to production")
        self.assertEqual(result["status"], "awaiting_human_approval")
        self.assertNotIn("execution", result)


if __name__ == "__main__":
    unittest.main()
