import unittest

from backend.app.evaluation.quality_recovery import recover_with_evaluation
from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.retry_policy import RetryPolicy


class TestStep54(unittest.TestCase):
    def _initial(self):
        return {
            "model": "initial-model",
            "status": "success",
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 4,
            "result": {
                "text": "unrelated",
                "model": "initial-model",
                "provider": "provider-a",
            },
        }

    def _review(self):
        return {
            "status": "review",
            "score": 0.5,
        }

    def _analysis(self):
        return {"task_type": "general"}

    def _routing(self):
        return {"model": "initial-model"}

    def test_recovery_uses_provider_boundary_and_preserves_grounding_context(self):
        calls = []

        def provider_executor(provider, model, task, context):
            calls.append((provider, model, task, context))
            return {
                "status": "completed",
                "execution_performed": True,
                "result": {
                    "text": "ai answer",
                    "model": model,
                    "provider": provider,
                },
            }

        budget = ExecutionBudget(max_attempts=2)
        result = recover_with_evaluation(
            task="ai",
            candidates=["initial-model", "recovery-model"],
            adapter_resolver=lambda _: None,
            analysis=self._analysis(),
            routing=self._routing(),
            initial_execution=self._initial(),
            initial_evaluation=self._review(),
            retry_policy=RetryPolicy(max_attempts=1),
            execution_budget=budget,
            context={"grounded": True},
            provider_name_resolver=lambda _: "provider-b",
            invocation_executor=provider_executor,
        )

        self.assertTrue(result["improved"])
        self.assertEqual(result["best"]["model"], "recovery-model")
        self.assertEqual(result["best"]["execution"]["status"], "success")
        self.assertEqual(result["best"]["execution"]["result"]["provider"], "provider-b")
        self.assertEqual(result["recovery_attempts"], 1)
        self.assertEqual(budget.used_attempts, 1)
        self.assertEqual(calls, [("provider-b", "recovery-model", "ai", {"grounded": True})])

    def test_provider_failure_retries_and_consumes_shared_budget(self):
        calls = []

        def provider_executor(provider, model, task, context):
            calls.append(model)
            return {
                "status": "failed",
                "execution_performed": True,
                "provider": provider,
                "model": model,
                "reason": "provider_execution_failed",
                "request": {
                    "provider_name": provider,
                    "model_name": model,
                    "task": task,
                    "context": context,
                },
            }

        budget = ExecutionBudget(max_attempts=2)
        result = recover_with_evaluation(
            task="ai",
            candidates=["initial-model", "recovery-model"],
            adapter_resolver=lambda _: None,
            analysis=self._analysis(),
            routing=self._routing(),
            initial_execution=self._initial(),
            initial_evaluation=self._review(),
            retry_policy=RetryPolicy(max_attempts=2),
            execution_budget=budget,
            provider_name_resolver=lambda _: "provider-b",
            invocation_executor=provider_executor,
        )

        self.assertFalse(result["improved"])
        self.assertEqual(result["recovery_attempts"], 2)
        self.assertEqual(result["candidates_tried"], ["recovery-model"])
        self.assertEqual(budget.used_attempts, 2)
        self.assertEqual(calls, ["recovery-model", "recovery-model"])

    def test_blocked_provider_does_not_consume_budget_or_mark_candidate_tried(self):
        calls = []

        def provider_executor(provider, model, task, context):
            calls.append(model)
            return {
                "status": "blocked",
                "execution_performed": False,
                "provider": provider,
                "model": model,
                "reason": "model_adapter_unavailable",
                "request": {
                    "provider_name": provider,
                    "model_name": model,
                    "task": task,
                    "context": context,
                },
            }

        budget = ExecutionBudget(max_attempts=1)
        result = recover_with_evaluation(
            task="ai",
            candidates=["initial-model", "blocked-model"],
            adapter_resolver=lambda _: None,
            analysis=self._analysis(),
            routing=self._routing(),
            initial_execution=self._initial(),
            initial_evaluation=self._review(),
            retry_policy=RetryPolicy(max_attempts=2),
            execution_budget=budget,
            provider_name_resolver=lambda _: "provider-b",
            invocation_executor=provider_executor,
        )

        self.assertFalse(result["improved"])
        self.assertEqual(result["recovery_attempts"], 0)
        self.assertEqual(result["candidates_tried"], [])
        self.assertEqual(budget.used_attempts, 0)
        self.assertEqual(calls, ["blocked-model"])

    def test_unknown_provider_identity_is_skipped_without_execution(self):
        calls = []

        def provider_executor(provider, model, task, context):
            calls.append(model)
            return {"status": "completed", "execution_performed": True}

        budget = ExecutionBudget(max_attempts=1)
        result = recover_with_evaluation(
            task="ai",
            candidates=["initial-model", "unknown-model"],
            adapter_resolver=lambda _: None,
            analysis=self._analysis(),
            routing=self._routing(),
            initial_execution=self._initial(),
            initial_evaluation=self._review(),
            retry_policy=RetryPolicy(max_attempts=1),
            execution_budget=budget,
            provider_name_resolver=lambda _: None,
            invocation_executor=provider_executor,
        )

        self.assertFalse(result["improved"])
        self.assertEqual(result["recovery_attempts"], 0)
        self.assertEqual(budget.used_attempts, 0)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
