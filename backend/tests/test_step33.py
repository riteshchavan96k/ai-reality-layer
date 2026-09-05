import unittest

from backend.app.evaluation.relevance import evaluate_relevance
from backend.app.evaluation.response_evaluator import evaluate_response


class TestStep33(unittest.TestCase):
    def test_relevance_detects_strong_term_overlap(self):
        result = evaluate_relevance(
            "Explain Python recursion",
            "Python recursion is a programming technique.",
        )

        self.assertEqual(result["score"], 1.0)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["matched_terms"], ["python", "recursion"])

    def test_relevance_detects_low_overlap(self):
        result = evaluate_relevance(
            "Explain database indexing",
            "The weather is sunny today.",
        )

        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["status"], "review")
        self.assertEqual(result["matched_terms"], [])

    def test_relevance_is_case_insensitive(self):
        result = evaluate_relevance(
            "Explain Python Classes",
            "Python classes group related data and behavior.",
        )

        self.assertEqual(result["score"], 1.0)

    def test_empty_response_gets_zero_relevance(self):
        result = evaluate_relevance("Explain databases", "")

        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["status"], "review")

    def test_response_evaluator_exposes_relevance(self):
        evaluation = evaluate_response(
            "Explain Python recursion",
            {
                "text": "Python recursion is a programming technique.",
                "model": "mock-model",
                "provider": "internal",
            },
            {"task_type": "programming"},
            {"model": "mock-model"},
        )

        self.assertIn("relevance", evaluation)
        self.assertEqual(evaluation["relevance"]["status"], "pass")
        self.assertGreaterEqual(evaluation["score"], 0.8)

    def test_missing_response_is_reviewed(self):
        evaluation = evaluate_response(
            "Explain databases",
            {"model": "mock-model", "provider": "internal", "text": ""},
            {"task_type": "general"},
            {"model": "mock-model"},
        )

        self.assertEqual(evaluation["status"], "review")
        self.assertEqual(evaluation["relevance"]["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
