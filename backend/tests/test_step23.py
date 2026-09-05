import unittest

from backend.app.evaluation.benchmark import run_benchmark
from backend.app.evaluation.response_evaluator import evaluate_response
from backend.app.orchestrator.orchestrator import orchestrate_task


class TestStep23(unittest.TestCase):
    def test_orchestrator_returns_evaluation(self):
        result = orchestrate_task("Tell me about AI")

        self.assertEqual(result["status"], "orchestrated")
        self.assertIn("evaluation", result)
        self.assertEqual(result["evaluation"]["status"], "pass")
        self.assertEqual(result["evaluation"]["score"], 1.0)

    def test_evaluator_detects_missing_response_text(self):
        evaluation = evaluate_response(
            "Tell me about AI",
            {"model": "mock-model", "provider": "internal", "text": ""},
            {"task_type": "general"},
            {"model": "mock-model"},
        )

        self.assertEqual(evaluation["status"], "review")
        self.assertLess(evaluation["score"], 1.0)
        self.assertFalse(evaluation["checks"]["non_empty_response"])

    def test_evaluator_exposes_structural_checks(self):
        result = orchestrate_task("Write Python code to reverse a string")
        evaluation = result["evaluation"]

        self.assertIn("non_empty_response", evaluation["checks"])
        self.assertIn("model_metadata_present", evaluation["checks"])
        self.assertIn("provider_metadata_present", evaluation["checks"])
        self.assertIn("limitation", evaluation)

    def test_benchmark_runs_all_cases(self):
        benchmark = run_benchmark()

        self.assertEqual(benchmark["benchmark"], "prototype-v1")
        self.assertEqual(benchmark["case_count"], 4)
        self.assertEqual(len(benchmark["cases"]), 4)
        self.assertEqual(benchmark["average_score"], 1.0)
        self.assertEqual(benchmark["pass_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
