import pytest

from backend.app.reality.retrieval_result_consumption import RetrievalResultConsumption
from backend.app.reality.retrieval_result_consumption_normalizer import (
    RetrievalResultConsumptionNormalizer,
)


def test_typed_consumption_is_preserved():
    result = RetrievalResultConsumption.usable_result("completed")

    assert RetrievalResultConsumptionNormalizer.normalize(result) is result


def test_usable_mapping_is_normalized():
    result = RetrievalResultConsumptionNormalizer.normalize(
        {
            "status": "usable",
            "retrieval_status": "completed",
            "usable": True,
        }
    )

    assert isinstance(result, RetrievalResultConsumption)
    assert result.status == "usable"
    assert result.usable is True


def test_rejected_mapping_preserves_reason():
    result = RetrievalResultConsumptionNormalizer.normalize(
        {
            "status": "rejected",
            "retrieval_status": "failed",
            "usable": False,
            "reason": "provider_timeout",
            "consumption_executed": True,
        }
    )

    assert result.reason == "provider_timeout"
    assert result.retrieval_status == "failed"


def test_missing_optional_fields_use_contract_defaults():
    result = RetrievalResultConsumptionNormalizer.normalize(
        {
            "status": "usable",
            "retrieval_status": "not_required",
            "usable": True,
        }
    )

    assert result.reason is None
    assert result.consumption_executed is True


def test_invalid_mapping_is_rejected():
    with pytest.raises((KeyError, ValueError)):
        RetrievalResultConsumptionNormalizer.normalize(
            {"status": "usable", "retrieval_status": "completed"}
        )


def test_inconsistent_mapping_is_rejected_by_contract():
    with pytest.raises(ValueError):
        RetrievalResultConsumptionNormalizer.normalize(
            {
                "status": "rejected",
                "retrieval_status": "completed",
                "usable": True,
            }
        )


def test_unsupported_shape_is_rejected():
    with pytest.raises(ValueError):
        RetrievalResultConsumptionNormalizer.normalize(["usable"])


def test_serialization_is_deterministic():
    result = RetrievalResultConsumptionNormalizer.normalize(
        {
            "status": "rejected",
            "retrieval_status": "blocked",
            "usable": False,
            "reason": "provider_unavailable",
        }
    )

    assert result.to_dict() == {
        "status": "rejected",
        "retrieval_status": "blocked",
        "usable": False,
        "reason": "provider_unavailable",
        "consumption_executed": True,
    }
