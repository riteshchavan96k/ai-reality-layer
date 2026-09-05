import unittest

from backend.app.execution.fallback_executor import execute_with_fallback
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.orchestrator.orchestrator import orchestrate_task


class AlwaysFailAdapter:
    def generate(self, task: str) -> dict:
        raise RuntimeError("primary unavailable")


class SuccessfulAdapter:
    def generate(self, task: str) -> dict:
        return {
            "text": f"Fallback response for: {task}",
            "model": "fallback-model",
            "provider": "test",
        }


class TestStep26(unittest.TestCase):
    def test_fallback_model_runs_after_primary_failure(self):
        adapters = {
            "primary": AlwaysFailAdapter(),
            "fallback": SuccessfulAdapter(),
        }

        result = execute_with_fallback(
            task="test task",
            model_names=["primary", "fallback"],
            adapter_resolver=adapters.get,
            retry_policy=RetryPolicy(max_attempts=1),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model"], "fallback")
        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["attempts_by_model"]["primary"], 1)
        self.assertEqual(result["attempts_by_model"]["fallback"], 1)

    def test_successful_primary_does_not_use_fallback(self):
        adapters = {
            "primary": SuccessfulAdapter(),
            "fallback": SuccessfulAdapter(),
        }

        result = execute_with_fallback(
            task="test task",
            model_names=["primary", "fallback"],
            adapter_resolver=adapters.get,
            retry_policy=RetryPolicy(max_attempts=1),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model"], "primary")
        self.assertFalse(result["fallback_used"])
        self.assertNotIn("fallback", result["attempts_by_model"])

    def test_missing_model_is_skipped_and_next_model_is_used(self):
        adapters = {"fallback": SuccessfulAdapter()}

        result = execute_with_fallback(
            task="test task",
            model_names=["missing", "fallback"],
            adapter_resolver=adapters.get,
            retry_policy=RetryPolicy(max_attempts=1),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model"], "fallback")
        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["attempts_by_model"]["missing"], 0)

    def test_all_models_failed_return_safe_failure(self):
        adapters = {
            "primary": AlwaysFailAdapter(),
            "fallback": AlwaysFailAdapter(),
        }

        result = execute_with_fallback(
            task="test task",
            model_names=["primary", "fallback"],
            adapter_resolver=adapters.get,
            retry_policy=RetryPolicy(max_attempts=2),
        )

        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["model"])
        self.assertEqual(result["attempts"], 4)
        self.assertEqual(result["attempts_by_model"]["primary"], 2)
        self.assertEqual(result["attempts_by_model"]["fallback"], 2)
        self.assertIn("primary", result["errors"])
        self.assertIn("fallback", result["errors"])

    def test_orchestrator_still_executes_normal_task(self):
        result = orchestrate_task("Tell me about AI")
        self.assertEqual(result["status"], "orchestrated")
        self.assertEqual(result["execution"]["model"], "mock-model")
        self.assertFalse(result["execution"]["fallback_used"])

    def test_human_approval_still_blocks_fallback_execution(self):
        result = orchestrate_task("Deploy this change to production")
        self.assertEqual(result["status"], "awaiting_human_approval")
        self.assertNotIn("execution", result)


if __name__ == "__main__":
    unittest.main()
