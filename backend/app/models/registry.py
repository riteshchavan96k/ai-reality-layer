from backend.app.models.capability_contract import ModelCapabilityContract
from backend.app.models.catalog import MODEL_CATALOG
from backend.app.models.provider_contract import get_provider_adapter
from backend.app.models.provider_execution_gate import ProviderExecutionGate


_CAPABILITY_CONTRACT = ModelCapabilityContract()
_EXECUTION_GATE = ProviderExecutionGate()


def _get_model_profile(model_name: str):
    catalog = _CAPABILITY_CONTRACT.normalize_catalog(MODEL_CATALOG)
    return catalog.get(model_name)


def get_model_provider_name(model_name: str) -> str | None:
    """Return the normalized provider identity declared for a model."""
    profile = _get_model_profile(model_name)
    if profile is None:
        return None
    return profile["provider"]


def get_model_adapter(model_name: str):
    profile = _get_model_profile(model_name)

    if profile is None:
        return None

    gate = _EXECUTION_GATE.check(profile["provider"])
    if gate["status"] != "allowed":
        return None

    provider = get_provider_adapter(profile["provider"])
    if provider is None:
        return None

    return provider.create_adapter(model_name, profile)
