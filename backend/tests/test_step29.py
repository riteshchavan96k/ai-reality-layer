import unittest

from backend.app.execution.outcome_memory import OutcomeMemory


class TestStep29(unittest.TestCase):
    def setUp(self):
        self.memory = OutcomeMemory(max_records=2)
        self.analysis = {"task_type": "programming"}
        self.routing = {"model": "mock-model"}
        self.execution = {
            "status": "success",
            "model": "mock-model",
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 2,
            "fallback_used": False,
        }
        self.evaluation = {"score": 1.0}

    def test_record_creates_structured_outcome(self):
        record = self.memory.record(
            "write python code",
            self.analysis,
            self.routing,
            self.execution,
            self.evaluation,
        )

        self.assertEqual(record["record_id"], 1)
        self.assertEqual(record["task_type"], "programming")
        self.assertEqual(record["routed_model"], "mock-model")
        self.assertEqual(record["executed_model"], "mock-model")
        self.assertEqual(record["evaluation_score"], 1.0)
        self.assertEqual(len(record["task_fingerprint"]), 64)
        self.assertNotIn("write python code", record.values())

    def test_recent_returns_copy(self):
        self.memory.record(
            "task one", self.analysis, self.routing, self.execution, self.evaluation
        )
        recent = self.memory.recent()
        recent[0]["task_type"] = "changed"

        self.assertEqual(self.memory.recent()[0]["task_type"], "programming")

    def test_memory_is_bounded(self):
        for task in ["task one", "task two", "task three"]:
            self.memory.record(
                task, self.analysis, self.routing, self.execution, self.evaluation
            )

        self.assertEqual(self.memory.size, 2)
        self.assertEqual([item["record_id"] for item in self.memory.recent()], [2, 3])

    def test_failed_execution_can_be_recorded_without_evaluation(self):
        failed_execution = {
            "status": "failed",
            "model": None,
            "attempts": 2,
            "total_attempts": 2,
            "budget_limit": 2,
            "fallback_used": True,
        }

        record = self.memory.record(
            "failed task",
            self.analysis,
            self.routing,
            failed_execution,
            None,
        )

        self.assertEqual(record["execution_status"], "failed")
        self.assertIsNone(record["evaluation_score"])
        self.assertTrue(record["fallback_used"])

    def test_invalid_configuration_and_limit(self):
        with self.assertRaises(ValueError):
            OutcomeMemory(max_records=0)

        with self.assertRaises(ValueError):
            self.memory.recent(0)


if __name__ == "__main__":
    unittest.main()
