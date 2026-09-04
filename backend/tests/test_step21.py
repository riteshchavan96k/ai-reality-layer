import unittest

from backend.app.orchestrator.orchestrator import orchestrate_task
from backend.app.router.model_router import route_task
from backend.app.router.model_selector import select_model
from backend.app.router.task_requirements import extract_requirements


class TestStep21(unittest.TestCase):
    def test_programming_requirement(self):
        self.assertEqual(extract_requirements("Write Python code"), ["programming"])

    def test_math_requirement(self):
        self.assertEqual(extract_requirements("Solve this equation"), ["reasoning"])

    def test_summarization_requirement(self):
        self.assertEqual(extract_requirements("Summarize this document"), ["long_context"])

    def test_general_requirement(self):
        self.assertEqual(extract_requirements("Tell me about AI"), ["general"])

    def test_selector_requirement_match(self):
        result = select_model(
            ["programming", "reasoning"],
            ["mock-model"],
        )
        self.assertEqual(result["selected_model"], "mock-model")
        self.assertEqual(result["scores"]["mock-model"], 0.5)

    def test_router_requirements(self):
        result = route_task("Write Python code to solve this equation", "programming")
        self.assertEqual(result["requirements"], ["programming", "reasoning"])
        self.assertEqual(result["model"], "mock-model")

    def test_orchestrator_requirement_aware_routing(self):
        result = orchestrate_task("Write Python code to solve this equation")
        self.assertEqual(result["status"], "orchestrated")
        self.assertEqual(
            result["routing"]["requirements"],
            ["programming", "reasoning"],
        )


if __name__ == "__main__":
    unittest.main()
