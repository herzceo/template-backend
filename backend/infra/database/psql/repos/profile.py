from typing import final
from uuid import UUID

from sqlalchemy import select

from backend.domain.entities.profile import Profile
from backend.domain.repos.profile import ProfileRepo
from backend.internal import Option

from .base import ImplCRUDSupported


@final
class ImplProfileRepo(ImplCRUDSupported[Profile], ProfileRepo):
    __slots__ = ()

    async def get_by_user_id(self, user_id: UUID) -> Option[Profile]:
        result = await self._session.execute(select(Profile).where(Profile.user_id == user_id))
        return Option(result.scalar_one_or_none())
