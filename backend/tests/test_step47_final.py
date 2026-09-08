from backend.app.models.provider_readiness import ProviderReadinessChecker


def test_readiness_output_contains_no_secret_value_fields():
    result = ProviderReadinessChecker().check("internal")
    assert "credential_configured" in result
    assert "endpoint_configured" in result
    assert "api_key" not in result
    assert "secret" not in result
