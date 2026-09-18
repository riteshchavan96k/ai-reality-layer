import pytest

from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumption_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumption_result_normalizer import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer,
)


def test_typed_result_passes_through_unchanged():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult.usable_result()
    normalized = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer.normalize(
        result
    )
    assert normalized is result


def test_usable_mapping_normalizes_to_canonical_result():
    normalized = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer.normalize(
        {
            "status": "usable",
            "authorization_status": "authorized",
            "allowed": True,
            "reason": None,
        }
    )
    assert normalized == GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult.usable_result()


def test_rejected_mapping_normalizes_and_preserves_reason():
    normalized = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer.normalize(
        {
            "status": "rejected",
            "authorization_status": "denied",
            "allowed": False,
            "reason": "authorization_decision_rejected",
        }
    )
    assert normalized.status == "rejected"
    assert normalized.authorization_status == "denied"
    assert normalized.allowed is False
    assert normalized.reason == "authorization_decision_rejected"
    assert normalized.decision_executed is True
    assert normalized.consumption_executed is True


def test_mapping_preserves_explicit_execution_flags():
    normalized = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer.normalize(
        {
            "status": "usable",
            "authorization_status": "authorized",
            "allowed": True,
            "decision_executed": True,
            "consumption_executed": False,
        }
    )
    with pytest.raises(ValueError, match="consumption_executed=True"):
        normalized


def test_mapping_rejects_invalid_contract_state():
    with pytest.raises(ValueError, match="requires a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer.normalize(
            {
                "status": "rejected",
                "authorization_status": "denied",
                "allowed": False,
            }
        )


def test_mapping_rejects_inconsistent_authorization_state():
    with pytest.raises(ValueError, match="denied status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer.normalize(
            {
                "status": "usable",
                "authorization_status": "denied",
                "allowed": True,
            }
        )


def test_mapping_rejects_invalid_status():
    with pytest.raises(ValueError, match="status must be usable or rejected"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer.normalize(
            {
                "status": "unknown",
                "authorization_status": "authorized",
                "allowed": True,
            }
        )


def test_non_mapping_input_is_rejected():
    with pytest.raises(ValueError, match="must be a result contract or mapping"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer.normalize(
            "invalid"
        )


def test_serialization_remains_deterministic():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer.normalize(
        {
            "status": "usable",
            "authorization_status": "authorized",
            "allowed": True,
        }
    )
    assert result.to_dict() == {
        "status": "usable",
        "authorization_status": "authorized",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
        "consumption_executed": True,
    }


def test_default_orchestration_dependencies_wire_the_normalizer():
    from backend.app.orchestrator.dependencies import OrchestrationDependencies

    dependencies = OrchestrationDependencies.default()
    assert isinstance(
        dependencies.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumption_result_normalizer,
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer,
    )


def test_normalizer_is_fail_closed_for_unexecuted_consumption():
    with pytest.raises(ValueError, match="consumption_executed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer.normalize(
            {
                "status": "usable",
                "authorization_status": "authorized",
                "allowed": True,
                "consumption_executed": False,
            }
        )
