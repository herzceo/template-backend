from typing import final
from uuid import UUID

from sqlalchemy import delete, select

from backend.domain.entities.session import Session
from backend.domain.repos.session import SessionRepo
from backend.internal import Option

from .base import ImplCRUDSupported


@final
class ImplSessionRepo(ImplCRUDSupported[Session], SessionRepo):
    __slots__ = ()

    async def get_by_token_hash(self, token_hash: str) -> Option[Session]:
        stmt = select(Session).where(Session.token_hash == token_hash)
        result = await self._session.execute(stmt)
        return Option(result.scalar_one_or_none())

    async def delete_by_user_id(self, user_id: UUID) -> None:
        stmt = delete(Session).where(Session.user_id == user_id)
        await self._session.execute(stmt)
