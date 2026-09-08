import unittest

from backend.app.models.response_contract import ModelResponseNormalizer
from backend.app.orchestrator.orchestrator import orchestrate_task
from backend.app.reality.retrieval_engine import RealityRetrievalEngine


class FakeRetrievalProvider:
    def retrieve(self, request: dict) -> dict:
        return {
            "status": "completed",
            "provider": "fake-provider",
            "sources": [{"title": "Example", "uri": "https://example.com"}],
            "content": "Current evidence.",
        }


class TestStep43ModelResponseContract(unittest.TestCase):
    def setUp(self):
        self.normalizer = ModelResponseNormalizer()

    def test_valid_response_is_normalized(self):
        result = self.normalizer.normalize(
            {"text": "answer", "model": "provider-model", "provider": "provider"},
            "fallback-model",
        )
        self.assertEqual(result["text"], "answer")
        self.assertEqual(result["model"], "provider-model")
        self.assertEqual(result["provider"], "provider")

    def test_model_name_is_used_when_response_omits_model(self):
        result = self.normalizer.normalize(
            {"text": "answer", "provider": "provider"},
            "fallback-model",
        )
        self.assertEqual(result["model"], "fallback-model")

    def test_grounding_metadata_is_preserved(self):
        grounding = {"status": "ready", "source_count": 1, "grounded": True}
        result = self.normalizer.normalize(
            {"text": "answer", "provider": "provider", "grounding": grounding},
            "mock-model",
        )
        self.assertEqual(result["grounding"], grounding)

    def test_non_dictionary_result_is_rejected(self):
        with self.assertRaises(ValueError):
            self.normalizer.normalize("answer", "mock-model")

    def test_empty_text_is_rejected(self):
        with self.assertRaises(ValueError):
            self.normalizer.normalize(
                {"text": "  ", "provider": "provider"},
                "mock-model",
            )

    def test_missing_provider_is_rejected(self):
        with self.assertRaises(ValueError):
            self.normalizer.normalize({"text": "answer"}, "mock-model")

    def test_invalid_grounding_metadata_is_rejected(self):
        with self.assertRaises(ValueError):
            self.normalizer.normalize(
                {"text": "answer", "provider": "provider", "grounding": "bad"},
                "mock-model",
            )

    def test_orchestrator_uses_normalized_model_response(self):
        result = orchestrate_task(
            "latest AI news",
            retrieval_engine=RealityRetrievalEngine(FakeRetrievalProvider()),
        )
        self.assertEqual(result["result"]["model"], "mock-model")
        self.assertEqual(result["result"]["provider"], "internal")
        self.assertTrue(result["result"]["text"].strip())


if __name__ == "__main__":
    unittest.main()
