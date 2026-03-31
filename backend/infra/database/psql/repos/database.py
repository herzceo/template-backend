from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from backend.domain.repos.database import Database

from .gateway import ImplRepoGateway

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction, async_sessionmaker


@final
class ImplDatabase(Database):
    __slots__ = ("_session", "_session_maker", "_txn_stack")

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._session_maker = session_maker
        self._session: AsyncSession | None = None
        self._txn_stack: list[AsyncSessionTransaction] = []

    @property
    def gateway(self) -> ImplRepoGateway:
        if self._session is None:
            msg = "Database.gateway accessed outside of an `async with db:` block"
            raise RuntimeError(msg)
        return ImplRepoGateway(self._session)

    def _assert_active(self) -> None:
        if not self._txn_stack:
            msg = "Database.commit()/rollback()/flush() called outside of an `async with db:` block"
            raise RuntimeError(msg)

    async def commit(self) -> None:
        self._assert_active()
        await self._txn_stack[-1].commit()

    async def rollback(self) -> None:
        self._assert_active()
        await self._txn_stack[-1].rollback()

    async def flush(self) -> None:
        self._assert_active()
        if self._session is None:
            msg = "Database.flush() called outside of an `async with db:` block"
            raise RuntimeError(msg)
        await self._session.flush()

    async def __aenter__(self) -> Self:
        if not self._txn_stack:
            self._session = self._session_maker()
            txn = await self._session.begin()
        else:
            if self._session is None:
                msg = "Nested `async with db:` but no session exists"
                raise RuntimeError(msg)
            txn = await self._session.begin_nested()
        self._txn_stack.append(txn)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        txn = self._txn_stack.pop()
        if txn.is_active:
            await txn.rollback()
        if not self._txn_stack and self._session is not None:
            await self._session.close()
            self._session = None
