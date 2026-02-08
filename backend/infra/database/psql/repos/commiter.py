from typing import final

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.repos.commiter import Commiter


@final
class ImplCommiter(Commiter):
    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def begin(self) -> None:
        await self._session.begin()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def flush(self) -> None:
        await self._session.flush()
