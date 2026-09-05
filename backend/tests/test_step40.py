import unittest

from backend.app.reality.evidence_quality import EvidenceQualityValidator


class TestStep40(unittest.TestCase):
    def setUp(self):
        self.validator = EvidenceQualityValidator()

    def test_completed_evidence_is_usable(self):
        result = self.validator.validate(
            {
                "status": "completed",
                "sources": [{"title": "Source A", "uri": "https://example.com/a"}],
                "content": "Current context",
            }
        )

        self.assertEqual(result["status"], "usable")
        self.assertTrue(result["usable"])
        self.assertEqual(result["source_count"], 1)
        self.assertTrue(result["has_content"])
        self.assertTrue(result["provenance_complete"])
        self.assertEqual(result["issues"], [])

    def test_title_only_source_is_valid_provenance(self):
        result = self.validator.validate(
            {
                "status": "completed",
                "sources": [{"title": "Official document", "uri": None}],
                "content": "Evidence content",
            }
        )

        self.assertTrue(result["usable"])
        self.assertTrue(result["provenance_complete"])

    def test_invalid_uri_makes_evidence_insufficient(self):
        result = self.validator.validate(
            {
                "status": "completed",
                "sources": [{"title": "Source A", "uri": "not-a-uri"}],
                "content": "Evidence content",
            }
        )

        self.assertEqual(result["status"], "insufficient")
        self.assertFalse(result["usable"])
        self.assertIn("source_invalid_uri", result["issues"])
        self.assertIn("incomplete_provenance", result["issues"])

    def test_missing_sources_are_insufficient(self):
        result = self.validator.validate(
            {"status": "completed", "sources": [], "content": "Evidence content"}
        )

        self.assertFalse(result["usable"])
        self.assertIn("no_sources", result["issues"])

    def test_missing_content_is_insufficient(self):
        result = self.validator.validate(
            {
                "status": "completed",
                "sources": [{"title": "Source A"}],
                "content": "   ",
            }
        )

        self.assertFalse(result["usable"])
        self.assertIn("no_content", result["issues"])

    def test_non_completed_retrieval_is_preserved_as_insufficient(self):
        result = self.validator.validate(
            {"status": "provider_unavailable", "sources": [], "content": None}
        )

        self.assertEqual(result["status"], "insufficient")
        self.assertFalse(result["usable"])
        self.assertIn("retrieval_not_completed", result["issues"])

    def test_not_required_retrieval_is_not_blocking_evidence(self):
        result = self.validator.validate(
            {"status": "not_required", "sources": [], "content": None}
        )

        self.assertEqual(result["status"], "not_required")
        self.assertFalse(result["usable"])
        self.assertEqual(result["issues"], [])

    def test_invalid_evidence_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            self.validator.validate(
                {"status": "completed", "sources": "bad", "content": "context"}
            )

    def test_invalid_source_item_is_rejected(self):
        with self.assertRaises(ValueError):
            self.validator.validate(
                {"status": "completed", "sources": ["bad"], "content": "context"}
            )


if __name__ == "__main__":
    unittest.main()
