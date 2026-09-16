import pytest

from backend.app.reality.grounding_execution_authorization_consumption_result import (
    GroundingExecutionAuthorizationConsumptionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_result_normalizer import (
    GroundingExecutionAuthorizationConsumptionResultNormalizer,
)


def test_typed_result_passes_through_unchanged() -> None:
    result = GroundingExecutionAuthorizationConsumptionResult.usable_result()
    normalized = GroundingExecutionAuthorizationConsumptionResultNormalizer.normalize(result)
    assert normalized is result


def test_authorized_mapping_normalizes_to_canonical_result() -> None:
    normalized = GroundingExecutionAuthorizationConsumptionResultNormalizer.normalize(
        {
            "status": "usable",
            "authorization_status": "authorized",
            "usable": True,
        }
    )
    assert normalized == GroundingExecutionAuthorizationConsumptionResult.usable_result()


def test_denied_mapping_preserves_reason() -> None:
    normalized = GroundingExecutionAuthorizationConsumptionResultNormalizer.normalize(
        {
            "status": "rejected",
            "authorization_status": "denied",
            "usable": False,
            "reason": "execution_not_authorized",
        }
    )
    assert normalized.reason == "execution_not_authorized"
    assert normalized.status == "rejected"
    assert normalized.authorization_status == "denied"
    assert normalized.usable is False


def test_mapping_uses_consumption_executed_default() -> None:
    normalized = GroundingExecutionAuthorizationConsumptionResultNormalizer.normalize(
        {
            "status": "usable",
            "authorization_status": "authorized",
            "usable": True,
        }
    )
    assert normalized.consumption_executed is True


def test_mapping_preserves_explicit_consumption_state() -> None:
    normalized = GroundingExecutionAuthorizationConsumptionResultNormalizer.normalize(
        {
            "status": "usable",
            "authorization_status": "authorized",
            "usable": True,
            "consumption_executed": False,
        }
    )
    assert normalized.consumption_executed is False


def test_invalid_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="result contract or mapping"):
        GroundingExecutionAuthorizationConsumptionResultNormalizer.normalize(object())


def test_missing_required_mapping_field_is_rejected() -> None:
    with pytest.raises(KeyError, match="status"):
        GroundingExecutionAuthorizationConsumptionResultNormalizer.normalize(
            {
                "authorization_status": "authorized",
                "usable": True,
            }
        )


def test_inconsistent_mapping_is_rejected_by_canonical_contract() -> None:
    with pytest.raises(ValueError, match="authorized status"):
        GroundingExecutionAuthorizationConsumptionResultNormalizer.normalize(
            {
                "status": "rejected",
                "authorization_status": "authorized",
                "usable": False,
                "reason": "invalid_authorization",
            }
        )


def test_empty_rejection_reason_is_rejected() -> None:
    with pytest.raises(ValueError, match="requires a reason"):
        GroundingExecutionAuthorizationConsumptionResultNormalizer.normalize(
            {
                "status": "rejected",
                "authorization_status": "denied",
                "usable": False,
                "reason": "   ",
            }
        )


def test_serialization_remains_deterministic_after_normalization() -> None:
    normalized = GroundingExecutionAuthorizationConsumptionResultNormalizer.normalize(
        {
            "status": "rejected",
            "authorization_status": "denied",
            "usable": False,
            "reason": "execution_not_authorized",
            "consumption_executed": True,
        }
    )
    assert normalized.to_dict() == {
        "status": "rejected",
        "authorization_status": "denied",
        "usable": False,
        "reason": "execution_not_authorized",
        "consumption_executed": True,
    }
