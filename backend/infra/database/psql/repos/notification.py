from typing import final
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.domain.entities.notification import Notification
from backend.domain.entities.notification_interaction import NotificationInteraction
from backend.domain.repos.notification import NotificationRepo
from backend.internal import Option

from .base import ImplCRUDSupported


@final
class ImplNotificationRepo(ImplCRUDSupported[Notification], NotificationRepo):
    __slots__ = ()

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> None:
        stmt = (
            pg_insert(NotificationInteraction)
            .values(
                notification_id=notification_id,
                user_id=user_id,
                read_at=func.now(),
            )
            .on_conflict_do_update(
                index_elements=["notification_id", "user_id"],
                set_={"read_at": func.now(), "updated_at": func.now()},
            )
        )
        await self._session.execute(stmt)

    async def mark_dismissed(self, notification_id: UUID, user_id: UUID) -> None:
        stmt = (
            pg_insert(NotificationInteraction)
            .values(
                notification_id=notification_id,
                user_id=user_id,
                dismissed_at=func.now(),
            )
            .on_conflict_do_update(
                index_elements=["notification_id", "user_id"],
                set_={"dismissed_at": func.now(), "updated_at": func.now()},
            )
        )
        await self._session.execute(stmt)

    async def set_reaction(
        self, notification_id: UUID, user_id: UUID, reaction: str | None
    ) -> None:
        stmt = (
            pg_insert(NotificationInteraction)
            .values(
                notification_id=notification_id,
                user_id=user_id,
                reaction=reaction,
            )
            .on_conflict_do_update(
                index_elements=["notification_id", "user_id"],
                set_={"reaction": reaction, "updated_at": func.now()},
            )
        )
        await self._session.execute(stmt)

    async def get_interaction(
        self, notification_id: UUID, user_id: UUID
    ) -> Option[NotificationInteraction]:
        stmt = select(NotificationInteraction).where(
            NotificationInteraction.notification_id == notification_id,
            NotificationInteraction.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return Option(result.scalar_one_or_none())

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
        include_dismissed: bool = False,
    ) -> list[tuple[Notification, NotificationInteraction | None]]:
        stmt = (
            select(Notification, NotificationInteraction)
            .outerjoin(
                NotificationInteraction,
                (NotificationInteraction.notification_id == Notification.id)
                & (NotificationInteraction.user_id == user_id),
            )
            .order_by(Notification.id)
            .offset(offset)
            .limit(limit)
        )
        if not include_dismissed:
            stmt = stmt.where(
                or_(
                    NotificationInteraction.dismissed_at.is_(None),
                    NotificationInteraction.notification_id.is_(None),
                )
            )
        result = await self._session.execute(stmt)
        return [(n, i) for n, i in result.all()]

    async def count_for_user(self, user_id: UUID, *, include_dismissed: bool = False) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .outerjoin(
                NotificationInteraction,
                (NotificationInteraction.notification_id == Notification.id)
                & (NotificationInteraction.user_id == user_id),
            )
        )
        if not include_dismissed:
            stmt = stmt.where(
                or_(
                    NotificationInteraction.dismissed_at.is_(None),
                    NotificationInteraction.notification_id.is_(None),
                )
            )
        result = await self._session.execute(stmt)
        return result.scalar_one()
