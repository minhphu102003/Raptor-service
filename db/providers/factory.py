from __future__ import annotations

from typing import Dict, Type

from .base import DatabaseConfig, IDatabaseProvider


class DatabaseProviderRegistry:
    """Registry for database providers"""

    def __init__(self):
        self._providers: Dict[str, Type[IDatabaseProvider]] = {}

    def register(self, provider_name: str, provider_class: Type[IDatabaseProvider]) -> None:
        """Register a database provider"""
        self._providers[provider_name] = provider_class

    def get_provider_class(self, provider_name: str) -> Type[IDatabaseProvider]:
        """Get a database provider class by name"""
        if provider_name not in self._providers:
            raise ValueError(f"Unknown database provider: {provider_name}")
        return self._providers[provider_name]

    def list_providers(self) -> list[str]:
        """List all registered providers"""
        return list(self._providers.keys())


# Global registry instance
_registry = DatabaseProviderRegistry()


class DatabaseFactory:
    """Factory for creating database providers"""

    @staticmethod
    def register_provider(provider_name: str, provider_class: Type[IDatabaseProvider]) -> None:
        """Register a new database provider"""
        _registry.register(provider_name, provider_class)

    @staticmethod
    def create_provider(config: DatabaseConfig) -> IDatabaseProvider:
        """Create a database provider based on configuration"""
        provider_class = _registry.get_provider_class(config.provider)
        return provider_class(config)

    @staticmethod
    def list_available_providers() -> list[str]:
        """List all available database providers"""
        return _registry.list_providers()

    @staticmethod
    def is_provider_available(provider_name: str) -> bool:
        """Check if a provider is available"""
        return provider_name in _registry.list_providers()


def register_provider(provider_name: str):
    """Decorator for registering database providers"""

    def decorator(provider_class: Type[IDatabaseProvider]) -> Type[IDatabaseProvider]:
        DatabaseFactory.register_provider(provider_name, provider_class)
        return provider_class

    return decorator
