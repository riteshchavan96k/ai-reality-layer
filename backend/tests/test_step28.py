import unittest

from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.fallback_executor import execute_with_fallback
from backend.app.execution.retry_policy import RetryPolicy


class AlwaysFailAdapter:
    def generate(self, task: str) -> dict:
        raise RuntimeError("temporary failure")


class SuccessfulAdapter:
    def generate(self, task: str) -> dict:
        return {
            "text": f"Response for: {task}",
            "model": "fallback-model",
            "provider": "test",
        }


class TestStep28(unittest.TestCase):
    def test_budget_tracks_remaining_attempts(self):
        budget = ExecutionBudget(max_attempts=4)
        self.assertEqual(budget.remaining_attempts, 4)
        budget.consume(2)
        self.assertEqual(budget.used_attempts, 2)
        self.assertEqual(budget.remaining_attempts, 2)

    def test_budget_rejects_invalid_configuration(self):
        with self.assertRaises(ValueError):
            ExecutionBudget(max_attempts=0)

        with self.assertRaises(ValueError):
            ExecutionBudget(max_attempts=2, used_attempts=3)

    def test_budget_rejects_over_consumption(self):
        budget = ExecutionBudget(max_attempts=2)
        with self.assertRaises(ValueError):
            budget.consume(3)

    def test_fallback_stops_when_total_budget_is_exhausted(self):
        adapters = {
            "primary": AlwaysFailAdapter(),
            "fallback": SuccessfulAdapter(),
        }

        result = execute_with_fallback(
            task="test task",
            model_names=["primary", "fallback"],
            adapter_resolver=adapters.get,
            retry_policy=RetryPolicy(max_attempts=2),
            execution_budget=ExecutionBudget(max_attempts=2),
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["total_attempts"], 2)
        self.assertEqual(result["budget_limit"], 2)
        self.assertEqual(result["attempts_by_model"]["primary"], 2)
        self.assertNotIn("fallback", result["attempts_by_model"])

    def test_budget_allows_fallback_with_remaining_attempts(self):
        adapters = {
            "primary": AlwaysFailAdapter(),
            "fallback": SuccessfulAdapter(),
        }

        result = execute_with_fallback(
            task="test task",
            model_names=["primary", "fallback"],
            adapter_resolver=adapters.get,
            retry_policy=RetryPolicy(max_attempts=2),
            execution_budget=ExecutionBudget(max_attempts=3),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model"], "fallback")
        self.assertEqual(result["total_attempts"], 3)
        self.assertEqual(result["budget_limit"], 3)
        self.assertEqual(result["attempts_by_model"]["primary"], 2)
        self.assertEqual(result["attempts_by_model"]["fallback"], 1)


if __name__ == "__main__":
    unittest.main()
