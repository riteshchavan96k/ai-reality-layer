from backend.app.reality.retrieval_provider_identity import RetrievalProviderIdentity


class RetrievalProviderIdentityResolver:
    """Resolve stable provider identity while preserving legacy provider names."""

    @staticmethod
    def resolve(provider: object) -> RetrievalProviderIdentity | None:
        identity = getattr(provider, "identity", None)
        if isinstance(identity, RetrievalProviderIdentity):
            return identity
        if isinstance(identity, str) and identity.strip():
            return RetrievalProviderIdentity(identity.strip())

        legacy_name = getattr(provider, "name", None)
        if isinstance(legacy_name, str) and legacy_name.strip():
            return RetrievalProviderIdentity(legacy_name.strip())

        return None


__all__ = ["RetrievalProviderIdentityResolver"]
