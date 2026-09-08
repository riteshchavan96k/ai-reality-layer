from backend.app.models.capability_contract import ModelCapabilityContract
from backend.app.models.catalog import MODEL_CATALOG
from backend.app.models.provider_contract import get_provider_adapter
from backend.app.models.provider_execution_gate import ProviderExecutionGate


_CAPABILITY_CONTRACT = ModelCapabilityContract()
_EXECUTION_GATE = ProviderExecutionGate()


def get_model_adapter(model_name: str):
    catalog = _CAPABILITY_CONTRACT.normalize_catalog(MODEL_CATALOG)
    profile = catalog.get(model_name)

    if profile is None:
        return None

    gate = _EXECUTION_GATE.check(profile["provider"])
    if gate["status"] != "allowed":
        return None

    provider = get_provider_adapter(profile["provider"])
    if provider is None:
        return None

    return provider.create_adapter(model_name, profile)
