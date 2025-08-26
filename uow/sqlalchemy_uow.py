from typing import Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self._session: Optional[AsyncSession] = None
        self._in_tx: bool = False

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UoW session is not started. Call begin() or use 'async with'.")
        return self._session

    async def begin(self) -> None:
        if self._session is not None:
            return
        self._session = self._session_factory()
        self._in_tx = True
        await self.session.begin()

    async def commit(self) -> None:
        if self._session is None:
            return
        try:
            await self.session.commit()
        finally:
            await self._close()

    async def rollback(self) -> None:
        if self._session is None:
            return
        try:
            await self.session.rollback()
        finally:
            await self._close()

    async def _close(self) -> None:
        self._in_tx = False
        await self.session.close()
        self._session = None

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        await self.begin()
        return self

    async def __aexit__(
        self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb
    ):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
