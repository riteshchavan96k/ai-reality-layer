import pytest

from backend.app.reality.grounding_execution_context_consumption_normalizer import (
    GroundingExecutionContextConsumptionResultNormalizer,
)
from backend.app.reality.grounding_execution_context_consumption_result import (
    GroundingExecutionContextConsumptionResult,
)


def test_typed_result_is_preserved():
    result = GroundingExecutionContextConsumptionResult.usable_result("ready")
    assert GroundingExecutionContextConsumptionResultNormalizer.normalize(result) is result


def test_usable_mapping_is_normalized():
    result = GroundingExecutionContextConsumptionResultNormalizer.normalize(
        {
            "status": "usable",
            "grounding_status": "ready",
            "usable": True,
            "reason": None,
            "consumption_executed": True,
        }
    )
    assert result == GroundingExecutionContextConsumptionResult.usable_result("ready")


def test_rejected_mapping_preserves_reason():
    result = GroundingExecutionContextConsumptionResultNormalizer.normalize(
        {
            "status": "rejected",
            "grounding_status": "ready",
            "usable": False,
            "reason": "execution_not_allowed",
        }
    )
    assert result.status == "rejected"
    assert result.reason == "execution_not_allowed"
    assert result.consumption_executed is True


def test_not_available_mapping_is_supported():
    result = GroundingExecutionContextConsumptionResultNormalizer.normalize(
        {
            "status": "usable",
            "grounding_status": "not_available",
            "usable": True,
        }
    )
    assert result.grounding_status == "not_available"
    assert result.usable is True


def test_explicit_execution_state_is_preserved():
    result = GroundingExecutionContextConsumptionResultNormalizer.normalize(
        {
            "status": "rejected",
            "grounding_status": "ready",
            "usable": False,
            "reason": "execution_context_not_prepared",
            "consumption_executed": False,
        }
    )
    assert result.consumption_executed is False


def test_invalid_mapping_is_rejected_by_contract():
    with pytest.raises(ValueError, match="usable status requires usable=True"):
        GroundingExecutionContextConsumptionResultNormalizer.normalize(
            {
                "status": "usable",
                "grounding_status": "ready",
                "usable": False,
            }
        )


def test_non_mapping_is_rejected():
    with pytest.raises(ValueError, match="must be a result contract or mapping"):
        GroundingExecutionContextConsumptionResultNormalizer.normalize("invalid")


def test_invalid_grounding_status_is_rejected():
    with pytest.raises(ValueError, match="grounding_status must be ready or not_available"):
        GroundingExecutionContextConsumptionResultNormalizer.normalize(
            {
                "status": "usable",
                "grounding_status": "unknown",
                "usable": True,
            }
        )


def test_invalid_reason_is_rejected():
    with pytest.raises(ValueError, match="requires a reason"):
        GroundingExecutionContextConsumptionResultNormalizer.normalize(
            {
                "status": "rejected",
                "grounding_status": "ready",
                "usable": False,
                "reason": "",
            }
        )


def test_serialization_is_deterministic():
    result = GroundingExecutionContextConsumptionResultNormalizer.normalize(
        {
            "status": "usable",
            "grounding_status": "ready",
            "usable": True,
        }
    )
    assert result.to_dict() == {
        "status": "usable",
        "grounding_status": "ready",
        "usable": True,
        "reason": None,
        "consumption_executed": True,
    }
