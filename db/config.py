from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from .providers.base import DatabaseConfig


class DatabaseProviderConfig(BaseModel):
    """Configuration for a specific database provider"""

    name: str = Field(description="Name identifier for this provider config")
    provider: str = Field(description="Provider type (postgresql, mongodb, etc.)")
    dsn: str = Field(description="Database connection string")
    options: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific options")
    ssl_config: Optional[Dict[str, Any]] = Field(default=None, description="SSL configuration")
    enabled: bool = Field(default=True, description="Whether this provider is enabled")
    description: Optional[str] = Field(default=None, description="Description of this provider")

    def to_database_config(self) -> DatabaseConfig:
        """Convert to DatabaseConfig object"""
        return DatabaseConfig(
            provider=self.provider, dsn=self.dsn, options=self.options, ssl_config=self.ssl_config
        )


class PerformanceTestConfig(BaseModel):
    """Configuration for performance testing"""

    enabled: bool = Field(default=False, description="Enable performance testing")
    test_duration_seconds: int = Field(default=60, description="Duration of each test in seconds")
    concurrent_connections: List[int] = Field(
        default=[1, 5, 10, 20], description="Connection counts to test"
    )
    test_queries: List[str] = Field(
        default=["SELECT 1", "SELECT count(*) FROM documents", "SELECT * FROM documents LIMIT 10"],
        description="Queries to run for performance testing",
    )
    metrics_collection_interval: int = Field(
        default=5, description="Metrics collection interval in seconds"
    )


class DatabaseManagerConfig(BaseSettings):
    """Enhanced configuration for database management with multi-provider support"""

    # Default provider
    default_provider: str = Field(default="primary", description="Default database provider to use")

    # Provider configurations
    providers: Dict[str, DatabaseProviderConfig] = Field(
        default_factory=dict, description="Available database providers"
    )

    # Performance testing
    performance_testing: PerformanceTestConfig = Field(
        default_factory=PerformanceTestConfig, description="Performance testing configuration"
    )

    # Migration settings
    auto_migrate: bool = Field(default=True, description="Auto-run migrations on startup")
    migration_timeout: int = Field(default=300, description="Migration timeout in seconds")

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        extra = "ignore"

    def get_provider_config(self, provider_name: Optional[str] = None) -> DatabaseProviderConfig:
        """Get configuration for a specific provider"""
        name = provider_name or self.default_provider

        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not found in configuration")

        config = self.providers[name]
        if not config.enabled:
            raise ValueError(f"Provider '{name}' is disabled")

        return config

    def get_enabled_providers(self) -> List[DatabaseProviderConfig]:
        """Get all enabled providers"""
        return [config for config in self.providers.values() if config.enabled]

    def add_provider(self, name: str, config: DatabaseProviderConfig) -> None:
        """Add a new provider configuration"""
        self.providers[name] = config

    def remove_provider(self, name: str) -> None:
        """Remove a provider configuration"""
        if name in self.providers:
            del self.providers[name]

    @classmethod
    def create_from_legacy_settings(
        cls, pg_async_dsn: str, vector_dsn: str
    ) -> "DatabaseManagerConfig":
        """Create configuration from legacy settings for backward compatibility"""
        primary_config = DatabaseProviderConfig(
            name="primary",
            provider="postgresql",
            dsn=pg_async_dsn,
            description="Primary PostgreSQL database",
        )

        return cls(default_provider="primary", providers={"primary": primary_config})


def create_test_configurations() -> DatabaseManagerConfig:
    """Create sample configurations for testing different databases"""

    # Primary PostgreSQL/Supabase
    primary_config = DatabaseProviderConfig(
        name="primary",
        provider="postgresql",
        dsn="postgresql+psycopg://user:pass@localhost:5432/raptor_primary",
        description="Primary PostgreSQL database",
    )

    # Alternative PostgreSQL for performance comparison
    alternative_config = DatabaseProviderConfig(
        name="alternative",
        provider="postgresql",
        dsn="postgresql+psycopg://user:pass@localhost:5433/raptor_alt",
        options={"disable_prepares": True},
        description="Alternative PostgreSQL for performance testing",
    )

    # Performance testing configuration
    perf_config = PerformanceTestConfig(
        enabled=True,
        test_duration_seconds=30,
        concurrent_connections=[1, 5, 10],
        test_queries=[
            "SELECT 1",
            "SELECT count(*) FROM documents",
            "SELECT doc_id, dataset_id FROM documents LIMIT 100",
            "SELECT d.doc_id, count(c.id) FROM documents d LEFT JOIN chunks c ON d.doc_id = c.doc_id GROUP BY d.doc_id LIMIT 50",
        ],
    )

    return DatabaseManagerConfig(
        default_provider="primary",
        providers={"primary": primary_config, "alternative": alternative_config},
        performance_testing=perf_config,
    )
