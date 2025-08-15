from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def build_session_factory(db_url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(db_url, pool_pre_ping=True, future=True)
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
