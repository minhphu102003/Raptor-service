from __future__ import annotations

import logging
from typing import Dict, Optional

from app.config import settings
from db.config import DatabaseManagerConfig, DatabaseProviderConfig
from db.providers.base import IDatabaseProvider
from db.providers.factory import DatabaseFactory
from db.providers.sqlalchemy_provider import PostgreSQLProvider, SupabaseProvider
from interfaces_adaptor.gateways.file_source import FileSourceHybrid
from repositories.document_repo_pg import DocumentRepoPg
from services.langchain.langchain_chunker import LangChainChunker
from uow.abstract_uow import AbstractUnitOfWork
from uow.sqlalchemy_uow import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)


class EnhancedContainer:
    """Enhanced dependency injection container with multi-database support"""

    def __init__(self, db_config: DatabaseManagerConfig):
        self.db_config = db_config
        self.file_source = FileSourceHybrid()
        self.vector_cfg = settings.vector

        # Initialize chunker
        self.chunker = LangChainChunker()
        self.chunk_fn = self.chunker.build()

        # Database providers
        self._providers: Dict[str, IDatabaseProvider] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all database providers"""
        if self._initialized:
            return

        logger.info("Initializing database providers...")

        for name, provider_config in self.db_config.providers.items():
            if not provider_config.enabled:
                logger.info(f"Skipping disabled provider: {name}")
                continue

            try:
                # Create provider
                provider = DatabaseFactory.create_provider(provider_config.to_database_config())
                await provider.initialize()

                # Test connectivity
                if await provider.health_check():
                    self._providers[name] = provider
                    logger.info(
                        f"Successfully initialized provider: {name} ({provider.provider_name})"
                    )
                else:
                    logger.warning(f"Health check failed for provider: {name}")

            except Exception as e:
                logger.error(f"Failed to initialize provider {name}: {e}")
                # Optionally continue with other providers or raise
                continue

        if not self._providers:
            raise RuntimeError("No database providers were successfully initialized")

        self._initialized = True
        logger.info(f"Initialized {len(self._providers)} database providers")

    async def close(self) -> None:
        """Close all database providers"""
        for name, provider in self._providers.items():
            try:
                await provider.close()
                logger.info(f"Closed provider: {name}")
            except Exception as e:
                logger.error(f"Error closing provider {name}: {e}")

        self._providers.clear()
        self._initialized = False

    def get_provider(self, provider_name: Optional[str] = None) -> IDatabaseProvider:
        """Get a specific database provider"""
        if not self._initialized:
            raise RuntimeError("Container not initialized. Call initialize() first.")

        name = provider_name or self.db_config.default_provider

        if name not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(f"Provider '{name}' not available. Available: {available}")

        return self._providers[name]

    def make_uow(self, provider_name: Optional[str] = None) -> AbstractUnitOfWork:
        """Create a Unit of Work with the specified or default provider"""
        provider = self.get_provider(provider_name)
        return SqlAlchemyUnitOfWork.from_provider(provider)

    def make_doc_repo(self, uow: AbstractUnitOfWork) -> DocumentRepoPg:
        """Create a document repository"""
        return DocumentRepoPg(uow)

    def list_providers(self) -> list[str]:
        """List all available providers"""
        return list(self._providers.keys())

    def get_default_provider_name(self) -> str:
        """Get the name of the default provider"""
        return self.db_config.default_provider

    async def get_all_provider_info(self) -> Dict[str, dict]:
        """Get connection info for all providers"""
        info = {}
        for name, provider in self._providers.items():
            try:
                info[name] = await provider.get_connection_info()
            except Exception as e:
                info[name] = {"error": str(e)}
        return info

    async def health_check_all(self) -> Dict[str, bool]:
        """Health check all providers"""
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception:
                results[name] = False
        return results

    @classmethod
    def create_from_legacy_settings(
        cls, orm_async_dsn: str, vector_dsn: str
    ) -> "EnhancedContainer":
        """Create container from legacy settings for backward compatibility"""
        db_config = DatabaseManagerConfig.create_from_legacy_settings(orm_async_dsn, vector_dsn)
        return cls(db_config)


class LegacyContainer:
    """Legacy container wrapper for backward compatibility"""

    def __init__(self, orm_async_dsn: str, vector_dsn: str):
        # Import legacy session builder
        from db.session import build_session_factory

        self.file_source = FileSourceHybrid()
        self.vector_cfg = settings.vector
        self.vector_dsn = vector_dsn
        self.session_factory = build_session_factory(orm_async_dsn)

        self.chunker = LangChainChunker()
        self.chunk_fn = self.chunker.build()

    def make_uow(self) -> SqlAlchemyUnitOfWork:
        """Create legacy SQLAlchemy UoW"""
        return SqlAlchemyUnitOfWork(self.session_factory)

    def make_doc_repo(self, uow: SqlAlchemyUnitOfWork) -> DocumentRepoPg:
        """Create document repository"""
        return DocumentRepoPg(uow)


# Re-export original Container as alias for backward compatibility
Container = LegacyContainer
