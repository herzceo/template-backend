from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.shared.db.database import Database
from backend.infra.dbus.psql.dbus import ImplDBus

from .gateway import ImplRepoGateway

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSessionTransaction


@final
class ImplDatabase(Database):
    __slots__ = ("_dbus", "_session", "_txn_stack")

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._session: AsyncSession = session_maker()
        self._txn_stack: list[AsyncSessionTransaction] = []
        self._dbus: ImplDBus | None = None

    @property
    def dbus(self) -> ImplDBus:
        if not self._txn_stack:
            msg = "Database.dbus accessed outside of an `async with db:` block"
            raise RuntimeError(msg)
        if self._dbus is None:
            self._dbus = ImplDBus(db=self, session=self._session)
        return self._dbus

    async def close(self) -> None:
        await self._session.close()

    @property
    def gateway(self) -> ImplRepoGateway:
        if not self._txn_stack:
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
        await self._session.flush()

    async def __aenter__(self) -> Self:
        if not self._txn_stack:
            txn = await self._session.begin()
        else:
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
            if not self._txn_stack:
                self._session.expunge_all()
            await txn.rollback()
