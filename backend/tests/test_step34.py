import unittest

from backend.app.evaluation.quality_recovery import recover_with_evaluation
from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.retry_policy import RetryPolicy


class FakeAdapter:
    def __init__(self, text: str, failures: int = 0) -> None:
        self.text = text
        self.failures = failures
        self.calls = 0

    def generate(self, task: str) -> dict:
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("transient failure")
        return {
            "text": self.text,
            "model": "fake-model",
            "provider": "test",
        }


class TestStep34(unittest.TestCase):
    def _initial(self, score: float = 0.4) -> dict:
        return {
            "status": "success",
            "model": "model-a",
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 4,
            "attempts_by_model": {"model-a": 1},
            "fallback_used": False,
            "result": {
                "text": "unrelated response",
                "model": "model-a",
                "provider": "test",
            },
        }

    def _evaluation(self, score: float = 0.4) -> dict:
        return {
            "score": score,
            "status": "review",
        }

    def test_reviewed_response_can_improve_with_alternative_model(self):
        adapters = {
            "model-a": FakeAdapter("unrelated response"),
            "model-b": FakeAdapter("Python recursion explained"),
        }

        result = recover_with_evaluation(
            task="Explain Python recursion",
            candidates=["model-a", "model-b"],
            adapter_resolver=lambda name: adapters.get(name),
            analysis={"task_type": "programming"},
            routing={"model": "model-a"},
            initial_execution=self._initial(),
            initial_evaluation=self._evaluation(),
            retry_policy=RetryPolicy(max_attempts=1),
            execution_budget=ExecutionBudget(max_attempts=2, used_attempts=1),
        )

        self.assertTrue(result["used"])
        self.assertTrue(result["improved"])
        self.assertEqual(result["best"]["model"], "model-b")
        self.assertGreater(result["best"]["evaluation"]["score"], 0.4)

    def test_passing_initial_evaluation_skips_recovery(self):
        adapter = FakeAdapter("good response")
        result = recover_with_evaluation(
            task="Explain Python recursion",
            candidates=["model-a", "model-b"],
            adapter_resolver=lambda name: adapter,
            analysis={"task_type": "programming"},
            routing={"model": "model-a"},
            initial_execution=self._initial(),
            initial_evaluation={"score": 0.9, "status": "pass"},
            retry_policy=RetryPolicy(max_attempts=1),
            execution_budget=ExecutionBudget(max_attempts=2, used_attempts=1),
        )

        self.assertFalse(result["used"])
        self.assertFalse(result.get("improved", False))
        self.assertEqual(adapter.calls, 0)

    def test_budget_prevents_quality_recovery(self):
        adapter = FakeAdapter("Python recursion explained")
        result = recover_with_evaluation(
            task="Explain Python recursion",
            candidates=["model-a", "model-b"],
            adapter_resolver=lambda name: adapter,
            analysis={"task_type": "programming"},
            routing={"model": "model-a"},
            initial_execution=self._initial(),
            initial_evaluation=self._evaluation(),
            retry_policy=RetryPolicy(max_attempts=1),
            execution_budget=ExecutionBudget(max_attempts=1, used_attempts=1),
        )

        self.assertFalse(result["used"])
        self.assertFalse(result["improved"])
        self.assertEqual(adapter.calls, 0)

    def test_failed_recovery_candidate_is_tracked_without_replacing_best(self):
        adapters = {
            "model-a": FakeAdapter("unrelated response"),
            "model-b": FakeAdapter("Python recursion explained", failures=1),
        }
        result = recover_with_evaluation(
            task="Explain Python recursion",
            candidates=["model-a", "model-b"],
            adapter_resolver=lambda name: adapters.get(name),
            analysis={"task_type": "programming"},
            routing={"model": "model-a"},
            initial_execution=self._initial(),
            initial_evaluation=self._evaluation(),
            retry_policy=RetryPolicy(max_attempts=1),
            execution_budget=ExecutionBudget(max_attempts=2, used_attempts=1),
        )

        self.assertTrue(result["used"])
        self.assertFalse(result["improved"])
        self.assertEqual(result["candidates_tried"], ["model-b"])


if __name__ == "__main__":
    unittest.main()
