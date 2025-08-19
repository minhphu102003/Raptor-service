import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def build_session_factory(
    dsn: str, *, disable_prepares: bool = False
) -> async_sessionmaker[AsyncSession]:
    if not dsn.startswith("postgresql+psycopg://"):
        raise ValueError("DSN phải dùng driver 'postgresql+psycopg' (psycopg v3).")

    sslroot = os.getenv("SUPABASE_SSLROOTCERT")
    if not sslroot:
        sslroot = str(Path(__file__).with_name("prod-ca-2021.crt"))

    connect_args = {
        "sslmode": "verify-full",
        "sslrootcert": sslroot,
    }
    if disable_prepares:
        connect_args["prepare_threshold"] = None

    engine = create_async_engine(
        dsn,
        pool_pre_ping=True,
        poolclass=NullPool,
        connect_args=connect_args,
    )
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
