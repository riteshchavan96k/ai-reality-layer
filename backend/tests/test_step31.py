import unittest

from backend.app.execution.outcome_memory import OutcomeMemory
from backend.app.router.routing_optimizer import AdaptiveRoutingOptimizer
from backend.app.router.model_router import route_task


class TestStep31(unittest.TestCase):
    def test_insufficient_history_is_explicit(self):
        memory = OutcomeMemory()
        optimizer = AdaptiveRoutingOptimizer(min_samples=2)

        result = optimizer.rank("programming", ["model-a", "model-b"], memory)

        self.assertTrue(result["exploration"])
        self.assertEqual(result["selected_model"], "model-a")
        self.assertTrue(all(item["confidence"] == "insufficient_data" for item in result["ranked_models"]))

    def test_historical_signals_rank_reliable_model_higher(self):
        memory = OutcomeMemory()
        analysis = {"task_type": "programming"}
        routing_a = {"model": "model-a"}
        routing_b = {"model": "model-b"}
        success_a = {
            "status": "success",
            "model": "model-a",
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 2,
            "fallback_used": False,
        }
        success_b = {
            "status": "success",
            "model": "model-b",
            "attempts": 2,
            "total_attempts": 2,
            "budget_limit": 2,
            "fallback_used": False,
        }

        for _ in range(2):
            memory.record("task a", analysis, routing_a, success_a, {"score": 1.0})
            memory.record("task b", analysis, routing_b, success_b, {"score": 0.5})

        result = AdaptiveRoutingOptimizer(min_samples=2).rank(
            "programming", ["model-b", "model-a"], memory
        )

        self.assertFalse(result["exploration"])
        self.assertEqual(result["selected_model"], "model-a")
        self.assertEqual(result["ranked_models"][0]["model"], "model-a")
        self.assertEqual(result["ranked_models"][0]["confidence"], "historical")

    def test_task_type_isolation(self):
        memory = OutcomeMemory()
        analysis = {"task_type": "mathematics"}
        execution = {
            "status": "success",
            "model": "math-model",
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 1,
            "fallback_used": False,
        }
        memory.record("math task", analysis, {"model": "math-model"}, execution, {"score": 1.0})
        memory.record("math task 2", analysis, {"model": "math-model"}, execution, {"score": 1.0})

        result = AdaptiveRoutingOptimizer(min_samples=2).rank(
            "programming", ["math-model", "other-model"], memory
        )

        self.assertTrue(result["exploration"])
        self.assertEqual(result["ranked_models"][0]["confidence"], "insufficient_data")

    def test_model_router_exposes_optimization_state(self):
        memory = OutcomeMemory()
        result = route_task(
            "write python code",
            "programming",
            outcome_memory=memory,
        )

        self.assertIn("optimization", result)
        self.assertEqual(result["optimization"]["status"], "exploring")
        self.assertTrue(result["optimization"]["exploration"])

    def test_invalid_min_samples_is_rejected(self):
        with self.assertRaises(ValueError):
            AdaptiveRoutingOptimizer(min_samples=0)


if __name__ == "__main__":
    unittest.main()
