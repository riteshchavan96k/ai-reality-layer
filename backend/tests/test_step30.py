import unittest

from backend.app.execution.outcome_memory import OutcomeMemory


class TestStep30(unittest.TestCase):
    def setUp(self):
        self.memory = OutcomeMemory(max_records=10)
        self.analysis = {"task_type": "programming"}
        self.routing = {"model": "primary-model"}

    def record(self, model, status, score, attempts, fallback=False):
        execution = {
            "status": status,
            "model": model,
            "attempts": attempts,
            "total_attempts": attempts,
            "budget_limit": 4,
            "fallback_used": fallback,
        }
        evaluation = {"score": score} if score is not None else None
        self.memory.record(
            "example task",
            self.analysis,
            self.routing,
            execution,
            evaluation,
        )

    def test_empty_statistics_are_safe(self):
        stats = self.memory.statistics()

        self.assertEqual(stats["total_records"], 0)
        self.assertEqual(stats["success_rate"], 0.0)
        self.assertIsNone(stats["average_score"])
        self.assertEqual(stats["by_model"], {})

    def test_statistics_aggregate_execution_signals(self):
        self.record("model-a", "success", 1.0, 1)
        self.record("model-a", "success", 0.8, 2, fallback=True)
        self.record("model-b", "failed", None, 2, fallback=True)

        stats = self.memory.statistics()

        self.assertEqual(stats["total_records"], 3)
        self.assertEqual(stats["successful"], 2)
        self.assertEqual(stats["failed"], 1)
        self.assertAlmostEqual(stats["success_rate"], 2 / 3)
        self.assertAlmostEqual(stats["average_score"], 0.9)
        self.assertAlmostEqual(stats["average_attempts"], 5 / 3)
        self.assertAlmostEqual(stats["fallback_rate"], 2 / 3)

    def test_model_statistics_support_routing_signals(self):
        self.record("model-a", "success", 1.0, 1)
        self.record("model-a", "success", 0.5, 3)
        self.record("model-b", "failed", None, 2)

        stats = self.memory.statistics()

        model_a = stats["by_model"]["model-a"]
        self.assertEqual(model_a["executions"], 2)
        self.assertEqual(model_a["successful"], 2)
        self.assertEqual(model_a["failed"], 0)
        self.assertEqual(model_a["success_rate"], 1.0)
        self.assertEqual(model_a["average_score"], 0.75)
        self.assertEqual(model_a["average_attempts"], 2.0)

        model_b = stats["by_model"]["model-b"]
        self.assertEqual(model_b["executions"], 1)
        self.assertEqual(model_b["success_rate"], 0.0)
        self.assertIsNone(model_b["average_score"])

    def test_statistics_do_not_store_or_return_raw_task_text(self):
        self.record("model-a", "success", 1.0, 1)

        stats = self.memory.statistics()

        self.assertNotIn("example task", str(stats))


if __name__ == "__main__":
    unittest.main()
