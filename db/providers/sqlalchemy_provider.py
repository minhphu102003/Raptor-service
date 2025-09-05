from __future__ import annotations

import os
from pathlib import Path
import time
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool  # Changed from NullPool

from .base import DatabaseConfig, IDatabaseProvider, ISessionProvider
from .factory import register_provider


class SqlAlchemySessionProvider(ISessionProvider):
    """Session provider for SQLAlchemy"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create_session(self) -> AsyncSession:
        """Create a new SQLAlchemy session"""
        return self.session_factory()

    async def close_session(self, session: AsyncSession) -> None:
        """Close a SQLAlchemy session"""
        await session.close()

    async def begin_transaction(self, session: AsyncSession) -> None:
        """Begin a transaction"""
        await session.begin()

    async def commit_transaction(self, session: AsyncSession) -> None:
        """Commit a transaction"""
        await session.commit()

    async def rollback_transaction(self, session: AsyncSession) -> None:
        """Rollback a transaction"""
        await session.rollback()


@register_provider("postgresql")
class PostgreSQLProvider(IDatabaseProvider):
    """PostgreSQL database provider using SQLAlchemy"""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._engine = None
        self._session_factory = None
        self._session_provider = None

    @property
    def provider_name(self) -> str:
        return "postgresql"

    @property
    def session_provider(self) -> ISessionProvider:
        if self._session_provider is None:
            raise RuntimeError("Provider not initialized. Call initialize() first.")
        return self._session_provider

    async def initialize(self) -> None:
        """Initialize the PostgreSQL provider"""
        if not self.config.dsn.startswith("postgresql+psycopg://"):
            raise ValueError("DSN phải dùng driver 'postgresql+psycopg' (psycopg v3).")

        # Setup SSL configuration
        sslroot = self.config.ssl_config.get("sslrootcert") if self.config.ssl_config else None
        if not sslroot:
            sslroot = os.getenv("SUPABASE_SSLROOTCERT")
        if not sslroot:
            sslroot = str(Path(__file__).parent.parent / "prod-ca-2021.crt")

        # Build connection arguments
        connect_args = {
            "sslmode": "verify-full",
            "sslrootcert": sslroot,
        }

        # Add custom options
        if self.config.options:
            if self.config.options.get("disable_prepares", False):
                connect_args["prepare_threshold"] = None
            connect_args.update(self.config.options.get("connect_args", {}))

        # Create engine with proper connection pooling
        self._engine = create_async_engine(
            self.config.dsn,
            pool_pre_ping=True,
            poolclass=AsyncAdaptedQueuePool,  # Use connection pooling
            pool_size=20,  # Number of connections to maintain in the pool
            max_overflow=30,  # Additional connections that can be created when needed
            pool_timeout=30,  # Seconds to wait before giving up on getting a connection
            pool_recycle=3600,  # Recycle connections after 1 hour
            connect_args=connect_args,
        )

        # Create session factory
        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

        # Create session provider
        self._session_provider = SqlAlchemySessionProvider(self._session_factory)

    async def close(self) -> None:
        """Close all connections and cleanup resources"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._session_provider = None

    async def health_check(self) -> bool:
        """Check if the database is healthy and accessible"""
        try:
            session = await self.session_provider.create_session()
            try:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
            finally:
                await self.session_provider.close_session(session)
        except Exception:
            return False

    async def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the current connection"""
        try:
            session = await self.session_provider.create_session()
            try:
                # Get database version
                version_result = await session.execute(text("SELECT version()"))
                version = version_result.scalar()

                # Get current database name
                db_result = await session.execute(text("SELECT current_database()"))
                database = db_result.scalar()

                # Get current user
                user_result = await session.execute(text("SELECT current_user"))
                user = user_result.scalar()

                return {
                    "provider": self.provider_name,
                    "version": version,
                    "database": database,
                    "user": user,
                    "dsn_host": self.config.dsn.split("@")[1].split("/")[0]
                    if "@" in self.config.dsn
                    else "unknown",
                }
            finally:
                await self.session_provider.close_session(session)
        except Exception as e:
            return {"provider": self.provider_name, "error": str(e)}

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for benchmarking"""
        metrics = {}

        try:
            session = await self.session_provider.create_session()
            try:
                # Test query performance
                start_time = time.time()
                await session.execute(text("SELECT 1"))
                query_time = time.time() - start_time

                # Get active connections
                connections_result = await session.execute(
                    text("""
                    SELECT count(*)
                    FROM pg_stat_activity
                    WHERE state = 'active'
                """)
                )
                active_connections = connections_result.scalar()

                # Get database size
                size_result = await session.execute(
                    text("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """)
                )
                database_size = size_result.scalar()

                # Get cache hit ratio
                cache_result = await session.execute(
                    text("""
                    SELECT
                        sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as cache_hit_ratio
                    FROM pg_statio_user_tables
                """)
                )
                cache_hit_ratio = cache_result.scalar()

                metrics = {
                    "simple_query_time_ms": query_time * 1000,
                    "active_connections": active_connections,
                    "database_size": database_size,
                    "cache_hit_ratio": float(cache_hit_ratio) if cache_hit_ratio else 0.0,
                    "timestamp": time.time(),
                }

            finally:
                await self.session_provider.close_session(session)

        except Exception as e:
            metrics["error"] = str(e)

        return metrics


@register_provider("supabase")
class SupabaseProvider(PostgreSQLProvider):
    """Supabase database provider (extends PostgreSQL provider)"""

    @property
    def provider_name(self) -> str:
        return "supabase"
