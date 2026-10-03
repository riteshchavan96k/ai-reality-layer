import unittest

from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer


class TestStep39(unittest.TestCase):
    def setUp(self):
        self.normalizer = RetrievalEvidenceNormalizer()

    def test_completed_retrieval_is_normalized(self):
        result = self.normalizer.normalize(
            {
                "status": "completed",
                "sources": [{"title": "Source A", "uri": "https://example.com/a"}],
                "content": "Current context",
            }
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["source_count"], 1)
        self.assertTrue(result["has_content"])
        self.assertEqual(result["sources"][0]["title"], "Source A")

    def test_source_shape_is_stable(self):
        result = self.normalizer.normalize(
            {
                "status": "completed",
                "sources": [
                    {"title": "Only title"},
                    {"uri": "https://example.com/b"},
                ],
                "content": "context",
            }
        )

        self.assertEqual(
            result["sources"],
            [
                {"title": "Only title", "uri": None},
                {"title": None, "uri": "https://example.com/b"},
            ],
        )

    def test_not_required_retrieval_remains_not_required(self):
        result = self.normalizer.normalize(
            {
                "status": "not_required",
                "sources": [],
                "content": None,
            }
        )

        self.assertEqual(result["status"], "not_required")
        self.assertEqual(result["source_count"], 0)
        self.assertFalse(result["has_content"])

    def test_blocked_retrieval_is_rejected_before_evidence_normalization(self):
        with self.assertRaises(ValueError):
            self.normalizer.normalize(
                {
                    "status": "blocked",
                    "sources": [],
                    "content": None,
                }
            )

    def test_completed_empty_result_is_invalid_evidence(self):
        result = self.normalizer.normalize(
            {
                "status": "completed",
                "sources": [],
                "content": None,
            }
        )

        self.assertEqual(result["status"], "invalid_evidence")

    def test_invalid_sources_are_rejected(self):
        with self.assertRaises(ValueError):
            self.normalizer.normalize(
                {"status": "completed", "sources": "bad", "content": "context"}
            )

    def test_invalid_source_item_is_rejected(self):
        with self.assertRaises(ValueError):
            self.normalizer.normalize(
                {"status": "completed", "sources": ["bad"], "content": "context"}
            )

    def test_source_without_provenance_is_rejected(self):
        with self.assertRaises(ValueError):
            self.normalizer.normalize(
                {"status": "completed", "sources": [{}], "content": "context"}
            )

    def test_invalid_content_type_is_rejected(self):
        with self.assertRaises(ValueError):
            self.normalizer.normalize(
                {"status": "completed", "sources": [], "content": 123}
            )


if __name__ == "__main__":
    unittest.main()
