import certifi
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def build_session_factory(dsn: str) -> async_sessionmaker[AsyncSession]:
    if dsn.startswith("postgresql+psycopg://") is False:
        raise ValueError("DSN phải dùng driver 'postgresql+psycopg' cho psycopg v3.")

    engine = create_async_engine(
        dsn,
        poolclass=NullPool,
        pool_pre_ping=True,
        connect_args={
            "prepare_threshold": None,
            "sslmode": "require",
            "sslrootcert": certifi.where(),
        },
    )
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
