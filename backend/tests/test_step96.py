import pytest

from backend.app.reality.grounding_context_consumption_normalizer import (
    GroundingContextConsumptionResultNormalizer,
)
from backend.app.reality.grounding_context_consumption_result import (
    GroundingContextConsumptionResult,
)


def test_typed_result_is_preserved() -> None:
    result = GroundingContextConsumptionResult.usable_result("ready")
    normalized = GroundingContextConsumptionResultNormalizer.normalize(result)
    assert normalized is result


def test_usable_mapping_is_normalized() -> None:
    normalized = GroundingContextConsumptionResultNormalizer.normalize(
        {
            "status": "usable",
            "grounding_status": "ready",
            "usable": True,
            "reason": None,
        }
    )
    assert normalized == GroundingContextConsumptionResult.usable_result("ready")


def test_rejected_mapping_preserves_reason() -> None:
    normalized = GroundingContextConsumptionResultNormalizer.normalize(
        {
            "status": "rejected",
            "grounding_status": "ready",
            "usable": False,
            "reason": "empty_grounding_context",
        }
    )
    assert normalized.reason == "empty_grounding_context"


def test_default_execution_state_is_true() -> None:
    normalized = GroundingContextConsumptionResultNormalizer.normalize(
        {"status": "usable", "grounding_status": "not_available", "usable": True}
    )
    assert normalized.consumption_executed is True


def test_invalid_mapping_is_rejected_by_contract() -> None:
    with pytest.raises(ValueError, match="usable status requires usable=True"):
        GroundingContextConsumptionResultNormalizer.normalize(
            {"status": "usable", "grounding_status": "ready", "usable": False}
        )


def test_non_mapping_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be a result contract or mapping"):
        GroundingContextConsumptionResultNormalizer.normalize("invalid")


def test_invalid_reason_is_rejected() -> None:
    with pytest.raises(ValueError, match="reason must be a nonempty string"):
        GroundingContextConsumptionResultNormalizer.normalize(
            {
                "status": "rejected",
                "grounding_status": "ready",
                "usable": False,
                "reason": "",
            }
        )


def test_serialization_is_deterministic() -> None:
    normalized = GroundingContextConsumptionResultNormalizer.normalize(
        {
            "status": "rejected",
            "grounding_status": "ready",
            "usable": False,
            "reason": "empty_grounding_context",
            "consumption_executed": True,
        }
    )
    assert normalized.to_dict() == {
        "status": "rejected",
        "grounding_status": "ready",
        "usable": False,
        "reason": "empty_grounding_context",
        "consumption_executed": True,
    }
