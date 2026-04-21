from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.domain.entities.notification import Notification
from backend.domain.entities.notification_interaction import NotificationInteraction
from backend.domain.repos.base import CRUDSupported
from backend.internal import Option


class NotificationRepo(CRUDSupported[Notification], Protocol):
    @abstractmethod
    async def mark_read(self, notification_id: UUID, user_id: UUID) -> None: ...

    @abstractmethod
    async def mark_dismissed(self, notification_id: UUID, user_id: UUID) -> None: ...

    @abstractmethod
    async def set_reaction(
        self, notification_id: UUID, user_id: UUID, reaction: str | None
    ) -> None: ...

    @abstractmethod
    async def get_interaction(
        self, notification_id: UUID, user_id: UUID
    ) -> Option[NotificationInteraction]: ...

    @abstractmethod
    async def list_for_user(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
        include_dismissed: bool = False,
    ) -> list[tuple[Notification, NotificationInteraction | None]]: ...

    @abstractmethod
    async def count_for_user(self, user_id: UUID, *, include_dismissed: bool = False) -> int: ...
