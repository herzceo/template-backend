from typing import final
from uuid import UUID

from sqlalchemy import insert, select

from backend.domain.entities.notification import Notification
from backend.domain.entities.notification_read import NotificationRead
from backend.domain.repos.notification import NotificationRepo

from .base import ImplCRUDSupported


@final
class ImplNotificationRepo(ImplCRUDSupported[Notification], NotificationRepo):
    __slots__ = ()

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> None:
        stmt = insert(NotificationRead).values(notification_id=notification_id, user_id=user_id)
        await self._session.execute(stmt)

    async def is_read(self, notification_id: UUID, user_id: UUID) -> bool:
        stmt = select(NotificationRead).where(
            NotificationRead.notification_id == notification_id,
            NotificationRead.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
