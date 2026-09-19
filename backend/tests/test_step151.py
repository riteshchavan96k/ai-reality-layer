import unittest

from backend.app.reality.retrieval_result_consumption import RetrievalResultConsumption
from backend.app.reality.retrieval_result_consumption_normalizer import (
    RetrievalResultConsumptionNormalizer,
)


class Step151RetrievalResultConsumptionContractTests(unittest.TestCase):
    def test_validate_accepts_canonical_contract(self):
        result = RetrievalResultConsumption.usable_result("completed")
        self.assertIs(RetrievalResultConsumption.validate(result), result)

    def test_validate_accepts_compatible_mapping(self):
        result = RetrievalResultConsumption.validate(
            {
                "status": "rejected",
                "retrieval_status": "failed",
                "usable": False,
                "reason": "upstream_failed",
                "consumption_executed": True,
            }
        )
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.retrieval_status, "failed")
        self.assertFalse(result.usable)

    def test_validate_rejects_missing_required_field(self):
        with self.assertRaisesRegex(ValueError, "missing required fields"):
            RetrievalResultConsumption.validate(
                {
                    "status": "usable",
                    "retrieval_status": "completed",
                    "usable": True,
                }
            )

    def test_validate_rejects_inconsistent_status_and_usable(self):
        with self.assertRaisesRegex(ValueError, "rejected status requires usable=False"):
            RetrievalResultConsumption.validate(
                {
                    "status": "rejected",
                    "retrieval_status": "failed",
                    "usable": True,
                    "consumption_executed": True,
                    "reason": "failed",
                }
            )

    def test_normalizer_delegates_mapping_validation_to_contract(self):
        with self.assertRaisesRegex(ValueError, "usable must be a boolean"):
            RetrievalResultConsumptionNormalizer.normalize(
                {
                    "status": "usable",
                    "retrieval_status": "completed",
                    "usable": "yes",
                    "consumption_executed": True,
                }
            )

    def test_normalizer_preserves_canonical_contract(self):
        result = RetrievalResultConsumption.rejected_result(
            "blocked", "retrieval_provider_unavailable"
        )
        self.assertIs(
            RetrievalResultConsumptionNormalizer.normalize(result),
            result,
        )


if __name__ == "__main__":
    unittest.main()
