from typing import Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.config import DatabaseProviderConfig
from db.providers.base import IDatabaseProvider
from db.providers.factory import DatabaseFactory
from db.providers.sqlalchemy_provider import PostgreSQLProvider

from .abstract_uow import AbstractUnitOfWork


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        # Legacy constructor - create a provider from session factory
        self._session_factory = session_factory

        # Create a minimal provider config for backward compatibility
        config = DatabaseProviderConfig(
            name="legacy",
            provider="postgresql",
            dsn="legacy://session_factory",  # Placeholder DSN
            description="Legacy SQLAlchemy session factory",
        )

        # Create a provider and configure it properly
        provider = PostgreSQLProvider(config.to_database_config())

        # Import the session provider class and create instance
        from db.providers.sqlalchemy_provider import SqlAlchemySessionProvider

        provider._session_provider = SqlAlchemySessionProvider(session_factory)

        # Set the session factory using proper typing to avoid type checker issues
        setattr(provider, "_session_factory", session_factory)

        super().__init__(provider)

        # Legacy attributes for backward compatibility
        self._session: Optional[AsyncSession] = None
        self._in_tx: bool = False

    @property
    def session(self) -> AsyncSession:
        # Use parent implementation but maintain backward compatibility
        return super().session

    async def begin(self) -> None:
        # Use parent implementation but sync legacy state
        await super().begin()
        self._session = super().session
        self._in_tx = True

    async def commit(self) -> None:
        # Use parent implementation but sync legacy state
        await super().commit()
        self._session = None
        self._in_tx = False

    async def rollback(self) -> None:
        # Use parent implementation but sync legacy state
        await super().rollback()
        self._session = None
        self._in_tx = False

    async def _close(self) -> None:
        # Use parent implementation
        await super()._close()
        self._session = None
        self._in_tx = False

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        await self.begin()
        return self

    async def __aexit__(
        self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb
    ):
        # Use parent implementation
        await super().__aexit__(exc_type, exc, tb)

    @classmethod
    def from_provider(cls, provider: IDatabaseProvider) -> "SqlAlchemyUnitOfWork":
        """Create UoW from a database provider"""
        # For new provider-based construction
        instance = cls.__new__(cls)
        AbstractUnitOfWork.__init__(instance, provider)
        instance._session = None
        instance._in_tx = False
        return instance
