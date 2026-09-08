import pytest

from backend.app.models.capability_contract import ModelCapabilityContract
from backend.app.models.catalog import MODEL_CATALOG
from backend.app.router.model_selector import select_model


CONTRACT = ModelCapabilityContract()


def test_normalize_model_profile():
    result = CONTRACT.normalize(
        "demo-model",
        {
            "name": "Demo Model",
            "provider": "demo-provider",
            "capabilities": ["reasoning", "general"],
        },
    )
    assert result == {
        "name": "Demo Model",
        "provider": "demo-provider",
        "capabilities": ["reasoning", "general"],
    }


def test_model_name_fills_missing_profile_name():
    result = CONTRACT.normalize(
        "demo-model",
        {"provider": "demo-provider", "capabilities": ["general"]},
    )
    assert result["name"] == "demo-model"


def test_duplicate_capabilities_are_removed_preserving_order():
    result = CONTRACT.normalize(
        "demo-model",
        {
            "provider": "demo-provider",
            "capabilities": ["reasoning", "general", "reasoning"],
        },
    )
    assert result["capabilities"] == ["reasoning", "general"]


def test_optional_metadata_is_preserved():
    result = CONTRACT.normalize(
        "demo-model",
        {
            "provider": "demo-provider",
            "capabilities": ["general"],
            "context_window": 128000,
            "supports_grounding": True,
        },
    )
    assert result["context_window"] == 128000
    assert result["supports_grounding"] is True


def test_missing_provider_is_rejected():
    with pytest.raises(ValueError, match="provider"):
        CONTRACT.normalize("demo-model", {"capabilities": ["general"]})


def test_invalid_capabilities_are_rejected():
    with pytest.raises(ValueError, match="capabilities"):
        CONTRACT.normalize(
            "demo-model",
            {"provider": "demo-provider", "capabilities": ["general", ""]},
        )


def test_catalog_normalizes_current_models():
    result = CONTRACT.normalize_catalog(MODEL_CATALOG)
    assert result["mock-model"]["provider"] == "internal"
    assert "reasoning" in result["mock-model"]["capabilities"]


def test_selector_uses_capability_contract_without_changing_scores():
    result = select_model(["programming"], ["mock-model"])
    assert result["selected_model"] == "mock-model"
    assert result["scores"]["mock-model"] == 1.0
