from backend.app.models.provider_contract import MockModelProvider


def test_provider_rejects_mismatched_profile_identity():
    provider = MockModelProvider()
    try:
        provider.create_adapter("mock-model", {"provider": "other"})
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("expected provider identity validation to fail")
