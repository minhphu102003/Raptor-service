from __future__ import annotations

import asyncio
import time
from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import QueuePool, StaticPool

from .base import DatabaseConfig, IDatabaseProvider, ISessionProvider
from .factory import register_provider
from .sqlalchemy_provider import SqlAlchemySessionProvider


@register_provider("postgresql_optimized")
class OptimizedPostgreSQLProvider(IDatabaseProvider):
    """Optimized PostgreSQL provider for performance comparison"""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._engine = None
        self._session_factory = None
        self._session_provider = None

    @property
    def provider_name(self) -> str:
        return "postgresql_optimized"

    @property
    def session_provider(self) -> ISessionProvider:
        if self._session_provider is None:
            raise RuntimeError("Provider not initialized. Call initialize() first.")
        return self._session_provider

    async def initialize(self) -> None:
        """Initialize with performance optimizations"""
        if not self.config.dsn.startswith("postgresql+psycopg://"):
            raise ValueError("DSN phải dùng driver 'postgresql+psycopg' (psycopg v3).")

        # Optimized connection arguments
        connect_args = {
            # Disable prepared statements for comparison
            "prepare_threshold": None,
            # Optimize for performance
            "server_side_cursors": False,
            "statement_cache_size": 0,
            # Connection optimization
            "tcp_keepalive": True,
            "tcp_keepalive_idle": 30,
            "tcp_keepalive_interval": 10,
            "tcp_keepalive_count": 3,
        }

        # SSL configuration
        if self.config.ssl_config:
            connect_args.update(self.config.ssl_config)

        # Add custom options
        if self.config.options:
            connect_args.update(self.config.options.get("connect_args", {}))

        # Create engine with optimized settings
        self._engine = create_async_engine(
            self.config.dsn,
            # Connection pool settings for performance
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            # Query optimization
            echo=False,
            connect_args=connect_args,
        )

        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

        self._session_provider = SqlAlchemySessionProvider(self._session_factory)

    async def close(self) -> None:
        """Close all connections"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._session_provider = None

    async def health_check(self) -> bool:
        """Health check with performance measurement"""
        try:
            session = await self.session_provider.create_session()
            try:
                start_time = time.time()
                result = await session.execute(text("SELECT 1"))
                query_time = time.time() - start_time

                # Consider healthy if query completes within 1 second
                return result.scalar() == 1 and query_time < 1.0
            finally:
                await self.session_provider.close_session(session)
        except Exception:
            return False

    async def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed connection information"""
        try:
            session = await self.session_provider.create_session()
            try:
                # Gather comprehensive connection info
                queries = {
                    "version": "SELECT version()",
                    "database": "SELECT current_database()",
                    "user": "SELECT current_user",
                    "client_encoding": "SELECT current_setting('client_encoding')",
                    "timezone": "SELECT current_setting('timezone')",
                    "max_connections": "SELECT current_setting('max_connections')",
                    "shared_buffers": "SELECT current_setting('shared_buffers')",
                    "work_mem": "SELECT current_setting('work_mem')",
                }

                info = {"provider": self.provider_name}

                for key, query in queries.items():
                    try:
                        result = await session.execute(text(query))
                        info[key] = result.scalar()
                    except Exception as e:
                        info[key] = f"Error: {e}"

                # Engine info
                if self._engine:
                    pool_info = {}
                    try:
                        # Try to get pool status safely
                        pool = self._engine.pool
                        pool_info["pool_size"] = getattr(pool, "_pool_size", "unknown")
                        pool_info["checked_in"] = len(getattr(pool, "_pool", []))
                        pool_info["checked_out"] = len(
                            getattr(pool, "_checked_out_connections", set())
                        )
                        pool_info["overflow"] = getattr(pool, "_overflow", 0)
                    except AttributeError:
                        # Fallback to basic engine info
                        pool_info["pool_configured"] = True
                        pool_info["pool_class"] = type(self._engine.pool).__name__

                    info.update(pool_info)

                return info
            finally:
                await self.session_provider.close_session(session)
        except Exception as e:
            return {"provider": self.provider_name, "error": str(e)}

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Enhanced performance metrics"""
        metrics = {}

        try:
            session = await self.session_provider.create_session()
            try:
                # Comprehensive performance queries
                perf_queries = {
                    "simple_query": "SELECT 1",
                    "current_timestamp": "SELECT current_timestamp",
                    "random_generation": "SELECT random()",
                    "math_operation": "SELECT sqrt(64) + sin(1.5)",
                }

                # Measure query performance
                for query_name, query in perf_queries.items():
                    start_time = time.time()
                    await session.execute(text(query))
                    metrics[f"{query_name}_time_ms"] = (time.time() - start_time) * 1000

                # Database performance metrics
                stats_queries = {
                    "active_connections": """
                        SELECT count(*) FROM pg_stat_activity WHERE state = 'active'
                    """,
                    "database_size": """
                        SELECT pg_size_pretty(pg_database_size(current_database()))
                    """,
                    "cache_hit_ratio": """
                        SELECT round(
                            sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100, 2
                        ) FROM pg_statio_user_tables
                    """,
                    "index_hit_ratio": """
                        SELECT round(
                            sum(idx_blks_hit) / NULLIF(sum(idx_blks_hit) + sum(idx_blks_read), 0) * 100, 2
                        ) FROM pg_statio_user_indexes
                    """,
                    "total_connections": """
                        SELECT count(*) FROM pg_stat_activity
                    """,
                    "locks_count": """
                        SELECT count(*) FROM pg_locks
                    """,
                }

                for metric_name, query in stats_queries.items():
                    try:
                        result = await session.execute(text(query))
                        value = result.scalar()
                        metrics[metric_name] = value if value is not None else 0
                    except Exception as e:
                        metrics[f"{metric_name}_error"] = str(e)

                # Connection pool metrics
                if self._engine:
                    pool_metrics = {}
                    try:
                        # Try to get pool status safely
                        pool = self._engine.pool
                        pool_metrics["pool_size"] = getattr(pool, "_pool_size", "unknown")
                        pool_metrics["pool_checked_in"] = len(getattr(pool, "_pool", []))
                        pool_metrics["pool_checked_out"] = len(
                            getattr(pool, "_checked_out_connections", set())
                        )
                        pool_metrics["pool_overflow"] = getattr(pool, "_overflow", 0)
                    except (AttributeError, TypeError):
                        # Fallback to basic info
                        pool_metrics["pool_configured"] = True
                        pool_metrics["pool_class"] = type(self._engine.pool).__name__

                    metrics.update(pool_metrics)

                metrics["timestamp"] = time.time()

            finally:
                await self.session_provider.close_session(session)

        except Exception as e:
            metrics["error"] = str(e)

        return metrics


@register_provider("sqlite_memory")
class SQLiteMemoryProvider(IDatabaseProvider):
    """In-memory SQLite provider for comparison testing"""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._engine = None
        self._session_factory = None
        self._session_provider = None

    @property
    def provider_name(self) -> str:
        return "sqlite_memory"

    @property
    def session_provider(self) -> ISessionProvider:
        if self._session_provider is None:
            raise RuntimeError("Provider not initialized. Call initialize() first.")
        return self._session_provider

    async def initialize(self) -> None:
        """Initialize SQLite in-memory database"""
        # Use in-memory SQLite
        dsn = "sqlite+aiosqlite:///:memory:"

        self._engine = create_async_engine(
            dsn,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False,
        )

        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

        self._session_provider = SqlAlchemySessionProvider(self._session_factory)

        # Initialize schema if needed
        # Note: This is a simplified example - you'd need to recreate your schema

    async def close(self) -> None:
        """Close SQLite connection"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._session_provider = None

    async def health_check(self) -> bool:
        """SQLite health check"""
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
        """Get SQLite connection info"""
        try:
            session = await self.session_provider.create_session()
            try:
                version_result = await session.execute(text("SELECT sqlite_version()"))
                return {
                    "provider": self.provider_name,
                    "version": version_result.scalar(),
                    "database": ":memory:",
                    "type": "sqlite_in_memory",
                }
            finally:
                await self.session_provider.close_session(session)
        except Exception as e:
            return {"provider": self.provider_name, "error": str(e)}

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """SQLite performance metrics"""
        metrics = {}

        try:
            session = await self.session_provider.create_session()
            try:
                # Simple performance test
                start_time = time.time()
                await session.execute(text("SELECT 1"))
                query_time = time.time() - start_time

                metrics = {
                    "simple_query_time_ms": query_time * 1000,
                    "database_type": "sqlite_memory",
                    "timestamp": time.time(),
                }

            finally:
                await self.session_provider.close_session(session)

        except Exception as e:
            metrics["error"] = str(e)

        return metrics
