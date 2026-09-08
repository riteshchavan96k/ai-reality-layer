from backend.app.models.provider_readiness import ProviderReadinessChecker


def test_ready_status_does_not_expose_credential_values():
    result = ProviderReadinessChecker().check("internal")
    assert "credential" in result
    assert "api_key" not in result
    assert "secret" not in result
