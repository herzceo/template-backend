from typing import final
from uuid import UUID

from sqlalchemy import select

from backend.domain.entities.user_email import UserEmail
from backend.domain.repos.user_email import UserEmailRepo
from backend.internal import Option

from .base import ImplCRUDSupported


@final
class ImplUserEmailRepo(ImplCRUDSupported[UserEmail], UserEmailRepo):
    __slots__ = ()

    async def get_by_normalized_email(self, normalized_email: str) -> Option[UserEmail]:
        stmt = select(UserEmail).where(UserEmail.normalized_email == normalized_email)
        result = await self._session.execute(stmt)
        return Option(result.scalar_one_or_none())

    async def list_by_user_id(self, user_id: UUID) -> list[UserEmail]:
        stmt = select(UserEmail).where(UserEmail.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_primary_for_user(self, user_id: UUID) -> Option[UserEmail]:
        stmt = select(UserEmail).where(
            UserEmail.user_id == user_id,
            UserEmail.is_primary.is_(True),
        )
        result = await self._session.execute(stmt)
        return Option(result.scalar_one_or_none())
