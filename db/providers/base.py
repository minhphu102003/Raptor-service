from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, runtime_checkable


@dataclass
class DatabaseConfig:
    """Configuration for database providers"""

    provider: str  # "postgresql", "mongodb", "sqlite", etc.
    dsn: str
    options: Optional[Dict[str, Any]] = None
    ssl_config: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.options is None:
            self.options = {}


@runtime_checkable
class ISessionProvider(Protocol):
    """Protocol for session management across different database types"""

    async def create_session(self) -> Any:
        """Create a new database session"""
        ...

    async def close_session(self, session: Any) -> None:
        """Close a database session"""
        ...

    async def begin_transaction(self, session: Any) -> None:
        """Begin a transaction"""
        ...

    async def commit_transaction(self, session: Any) -> None:
        """Commit a transaction"""
        ...

    async def rollback_transaction(self, session: Any) -> None:
        """Rollback a transaction"""
        ...


class IDatabaseProvider(ABC):
    """Abstract base class for database providers"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._session_provider: Optional[ISessionProvider] = None

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the database provider"""
        pass

    @property
    @abstractmethod
    def session_provider(self) -> ISessionProvider:
        """Get the session provider for this database"""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the database provider"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close all connections and cleanup resources"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the database is healthy and accessible"""
        pass

    @abstractmethod
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the current connection"""
        pass

    # Performance monitoring methods
    @abstractmethod
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for benchmarking"""
        pass
