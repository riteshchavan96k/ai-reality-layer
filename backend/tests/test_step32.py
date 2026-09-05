import os
import tempfile
import unittest

from backend.app.execution.persistent_outcome_memory import PersistentOutcomeMemory


class TestPersistentOutcomeMemory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "outcomes.db")
        self.analysis = {"task_type": "programming", "confidence": 0.5}
        self.routing = {"model": "model-a"}
        self.execution = {
            "status": "success",
            "model": "model-a",
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 2,
            "fallback_used": False,
        }
        self.evaluation = {"score": 0.9}

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_invalid_database_path(self):
        with self.assertRaises(ValueError):
            PersistentOutcomeMemory("")

    def test_record_persists_across_instances(self):
        first = PersistentOutcomeMemory(self.database_path)
        record = first.record(
            "write python code",
            self.analysis,
            self.routing,
            self.execution,
            self.evaluation,
        )

        second = PersistentOutcomeMemory(self.database_path)
        recent = second.recent()

        self.assertEqual(second.size, 1)
        self.assertEqual(recent[0]["record_id"], record["record_id"])
        self.assertEqual(recent[0]["evaluation_score"], 0.9)

    def test_raw_task_text_is_not_stored(self):
        memory = PersistentOutcomeMemory(self.database_path)
        memory.record(
            "secret task text should never be stored",
            self.analysis,
            self.routing,
            self.execution,
            self.evaluation,
        )

        with open(self.database_path, "rb") as database_file:
            database_bytes = database_file.read()

        self.assertNotIn(b"secret task text should never be stored", database_bytes)

    def test_routing_signals_are_task_type_specific(self):
        memory = PersistentOutcomeMemory(self.database_path)
        memory.record("task one", self.analysis, self.routing, self.execution, self.evaluation)
        memory.record(
            "task two",
            {"task_type": "mathematics"},
            {"model": "model-b"},
            {**self.execution, "model": "model-b"},
            {"score": 0.8},
        )

        signals = memory.routing_signals("programming")

        self.assertIn("model-a", signals)
        self.assertNotIn("model-b", signals)

    def test_statistics_match_persisted_records(self):
        memory = PersistentOutcomeMemory(self.database_path)
        memory.record("task one", self.analysis, self.routing, self.execution, self.evaluation)
        memory.record(
            "task two",
            self.analysis,
            {"model": "model-a"},
            {**self.execution, "status": "failed", "model": "model-a", "total_attempts": 2},
            None,
        )

        stats = memory.statistics()

        self.assertEqual(stats["total_records"], 2)
        self.assertEqual(stats["successful"], 1)
        self.assertEqual(stats["failed"], 1)
        self.assertEqual(stats["by_model"]["model-a"]["executions"], 2)

    def test_recent_returns_oldest_to_newest(self):
        memory = PersistentOutcomeMemory(self.database_path)
        first = memory.record("task one", self.analysis, self.routing, self.execution, self.evaluation)
        second = memory.record("task two", self.analysis, self.routing, self.execution, self.evaluation)

        recent = memory.recent(2)

        self.assertEqual([item["record_id"] for item in recent], [first["record_id"], second["record_id"]])


if __name__ == "__main__":
    unittest.main()
