from backend.app.models.capability_contract import ModelCapabilityContract
from backend.app.models.catalog import MODEL_CATALOG
from backend.app.models.provider_contract import get_provider_adapter


_CAPABILITY_CONTRACT = ModelCapabilityContract()


def get_model_adapter(model_name: str):
    catalog = _CAPABILITY_CONTRACT.normalize_catalog(MODEL_CATALOG)
    profile = catalog.get(model_name)

    if profile is None:
        return None

    provider = get_provider_adapter(profile["provider"])
    if provider is None:
        return None

    return provider.create_adapter(model_name, profile)
