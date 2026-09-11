import unittest

from backend.app.reality.retrieval_provider_registry import RetrievalProviderRegistry


class ProviderA:
    pass


class ProviderB:
    pass


class Step62RetrievalProviderRegistryBoundaryTests(unittest.TestCase):
    def test_registry_returns_registered_provider(self):
        provider = ProviderA()
        registry = RetrievalProviderRegistry()
        registry.register("live_web", provider)

        self.assertIs(registry.get("live_web"), provider)

    def test_registry_returns_default_for_unregistered_source_type(self):
        default = ProviderA()
        registry = RetrievalProviderRegistry(default_provider=default)

        self.assertIs(registry.get("unknown"), default)

    def test_registry_register_replaces_existing_provider(self):
        first = ProviderA()
        second = ProviderB()
        registry = RetrievalProviderRegistry({"live_web": first}, default_provider=None)

        registry.register("live_web", second)

        self.assertIs(registry.get("live_web"), second)

    def test_registry_normalizes_source_type_whitespace(self):
        provider = ProviderA()
        registry = RetrievalProviderRegistry()

        registry.register("  live_web  ", provider)

        self.assertIs(registry.get("live_web"), provider)

    def test_registry_rejects_invalid_source_type(self):
        registry = RetrievalProviderRegistry()

        with self.assertRaises(ValueError):
            registry.get("")

        with self.assertRaises(ValueError):
            registry.register("   ", ProviderA())

        with self.assertRaises(ValueError):
            registry.get(None)

    def test_default_provider_is_explicitly_exposed(self):
        default = ProviderA()
        registry = RetrievalProviderRegistry(default_provider=default)

        self.assertIs(registry.default_provider(), default)


if __name__ == "__main__":
    unittest.main()
