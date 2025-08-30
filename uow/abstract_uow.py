from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional, Type

from db.providers.base import IDatabaseProvider, ISessionProvider


class AbstractUnitOfWork(ABC):
    """Abstract Unit of Work that can work with any database provider"""

    def __init__(self, database_provider: IDatabaseProvider):
        self.database_provider = database_provider
        self._session: Optional[Any] = None
        self._in_tx: bool = False

    @property
    def session_provider(self) -> ISessionProvider:
        """Get the session provider"""
        return self.database_provider.session_provider

    @property
    def session(self) -> Any:
        """Get the current session"""
        if self._session is None:
            raise RuntimeError("UoW session is not started. Call begin() or use 'async with'.")
        return self._session

    @property
    def provider_name(self) -> str:
        """Get the name of the database provider"""
        return self.database_provider.provider_name

    async def begin(self) -> None:
        """Begin a new transaction"""
        if self._session is not None:
            return

        self._session = await self.session_provider.create_session()
        self._in_tx = True
        await self.session_provider.begin_transaction(self._session)

    async def commit(self) -> None:
        """Commit the current transaction"""
        if self._session is None:
            return

        try:
            await self.session_provider.commit_transaction(self._session)
        finally:
            await self._close()

    async def rollback(self) -> None:
        """Rollback the current transaction"""
        if self._session is None:
            return

        try:
            await self.session_provider.rollback_transaction(self._session)
        finally:
            await self._close()

    async def _close(self) -> None:
        """Close the current session"""
        if self._session is not None:
            self._in_tx = False
            await self.session_provider.close_session(self._session)
            self._session = None

    async def __aenter__(self) -> "AbstractUnitOfWork":
        await self.begin()
        return self

    async def __aexit__(
        self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Any
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    # Health and monitoring methods
    async def health_check(self) -> bool:
        """Check if the database connection is healthy"""
        return await self.database_provider.health_check()

    async def get_connection_info(self) -> dict[str, Any]:
        """Get information about the current database connection"""
        return await self.database_provider.get_connection_info()

    async def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics from the database provider"""
        return await self.database_provider.get_performance_metrics()


class GenericUnitOfWork(AbstractUnitOfWork):
    """Generic Unit of Work implementation that works with any database provider"""

    def __init__(self, database_provider: IDatabaseProvider):
        super().__init__(database_provider)

    def __repr__(self) -> str:
        return f"GenericUnitOfWork(provider={self.provider_name})"
