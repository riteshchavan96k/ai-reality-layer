from backend.app.models.provider_readiness import ProviderReadinessChecker


def test_readiness_contract_has_stable_fields():
    result = ProviderReadinessChecker().check("internal")
    assert set(result) == {"status", "provider", "adapter_available", "credential_configured", "endpoint_configured"}
