from __future__ import annotations

from typing import TYPE_CHECKING

from backend.app.shared.db.dbus import DBus
from backend.infra.database.psql import ImplDatabase
from tests.integration.mocks.dbus import MockDBus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class TestImplDatabase(ImplDatabase):
    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        mock_dbus: MockDBus,
    ) -> None:
        super().__init__(session_maker)
        self._mock_dbus = mock_dbus

    @property
    def dbus(self) -> DBus:
        if not self._txn_stack:
            msg = "Database.dbus accessed outside of an `async with db:` block"
            raise RuntimeError(msg)
        return self._mock_dbus
