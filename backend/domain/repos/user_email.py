from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.domain.entities.user_email import UserEmail
from backend.domain.repos.base import CRUDSupported
from backend.internal import Option


class UserEmailRepo(CRUDSupported[UserEmail], Protocol):
    @abstractmethod
    async def get_by_normalized_email(self, normalized_email: str) -> Option[UserEmail]: ...

    @abstractmethod
    async def list_by_user_id(self, user_id: UUID) -> list[UserEmail]: ...

    @abstractmethod
    async def get_primary_for_user(self, user_id: UUID) -> Option[UserEmail]: ...
