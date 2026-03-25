from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.domain.entities.notification import Notification
from backend.domain.repos.base import CRUDSupported


class NotificationRepo(CRUDSupported[Notification], Protocol):
    @abstractmethod
    async def mark_read(self, notification_id: UUID, user_id: UUID) -> None: ...

    @abstractmethod
    async def is_read(self, notification_id: UUID, user_id: UUID) -> bool: ...
