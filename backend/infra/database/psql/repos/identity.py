from typing import final
from uuid import UUID

from sqlalchemy import delete, select

from backend.domain.entities.identity import Identity
from backend.domain.enums import IdentityProvider
from backend.domain.repos.identity import IdentityRepo
from backend.internal import Option

from .base import ImplCRUDSupported


@final
class ImplIdentityRepo(ImplCRUDSupported[Identity], IdentityRepo):
    __slots__ = ()

    async def get_by_provider_subject(
        self, provider: IdentityProvider, provider_subject_id: str
    ) -> Option[Identity]:
        stmt = select(Identity).where(
            Identity.provider == provider,
            Identity.provider_subject_id == provider_subject_id,
        )
        result = await self._session.execute(stmt)
        return Option(result.scalar_one_or_none())

    async def list_by_user_id(self, user_id: UUID) -> list[Identity]:
        stmt = select(Identity).where(Identity.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_user_and_provider(self, user_id: UUID, provider: IdentityProvider) -> None:
        stmt = delete(Identity).where(
            Identity.user_id == user_id,
            Identity.provider == provider,
        )
        await self._session.execute(stmt)
