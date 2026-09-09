import unittest

from backend.app.execution.execution_budget import ExecutionBudget
from backend.app.execution.fallback_executor import execute_with_fallback
from backend.app.execution.retry_policy import RetryPolicy
from backend.app.orchestrator.orchestrator import orchestrate_task
from backend.app.models.registry import get_model_provider_name


class TestStep53(unittest.TestCase):
    def test_fallback_can_execute_through_provider_invocation_boundary(self):
        calls = []

        def provider_executor(provider, model, task, context):
            calls.append((provider, model, task, context))
            return {
                "status": "completed",
                "execution_performed": True,
                "result": {
                    "text": "provider-boundary response",
                    "model": model,
                    "provider": provider,
                },
            }

        result = execute_with_fallback(
            task="hello",
            model_names=["model-a"],
            adapter_resolver=lambda _: None,
            retry_policy=RetryPolicy(max_attempts=1),
            execution_budget=ExecutionBudget(max_attempts=1),
            context={"grounded": True},
            provider_name_resolver=lambda _: "provider-a",
            invocation_executor=provider_executor,
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model"], "model-a")
        self.assertEqual(result["result"]["provider"], "provider-a")
        self.assertEqual(calls, [("provider-a", "model-a", "hello", {"grounded": True})])

    def test_provider_failure_is_retried_without_exposing_provider_details(self):
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

        result = execute_with_fallback(
            task="hello",
            model_names=["model-a"],
            adapter_resolver=lambda _: None,
            retry_policy=RetryPolicy(max_attempts=2),
            execution_budget=ExecutionBudget(max_attempts=2),
            provider_name_resolver=lambda _: "provider-a",
            invocation_executor=provider_executor,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts_by_model"]["model-a"], 2)
        self.assertEqual(calls, ["model-a", "model-a"])
        self.assertNotIn("provider detail", str(result))

    def test_blocked_provider_attempt_consumes_no_execution_budget(self):
        calls = []

        def provider_executor(provider, model, task, context):
            calls.append(model)
            if model == "blocked-model":
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
            return {
                "status": "completed",
                "execution_performed": True,
                "result": {
                    "text": "fallback response",
                    "model": model,
                    "provider": provider,
                },
            }

        result = execute_with_fallback(
            task="hello",
            model_names=["blocked-model", "working-model"],
            adapter_resolver=lambda _: None,
            retry_policy=RetryPolicy(max_attempts=2),
            execution_budget=ExecutionBudget(max_attempts=1),
            provider_name_resolver=lambda _: "provider-a",
            invocation_executor=provider_executor,
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model"], "working-model")
        self.assertEqual(result["attempts_by_model"]["blocked-model"], 0)
        self.assertEqual(result["attempts_by_model"]["working-model"], 1)
        self.assertEqual(calls, ["blocked-model", "working-model"])

    def test_unknown_model_has_no_provider_identity(self):
        self.assertIsNone(get_model_provider_name("missing-model"))

    def test_orchestrator_uses_provider_execution_boundary(self):
        result = orchestrate_task("Tell me about AI")

        self.assertEqual(result["status"], "orchestrated")
        self.assertEqual(result["execution"]["model"], "mock-model")
        self.assertEqual(result["result"]["provider"], "internal")
        self.assertEqual(result["result"]["model"], "mock-model")


if __name__ == "__main__":
    unittest.main()
