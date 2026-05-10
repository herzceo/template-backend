from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.domain.entities.profile import Profile
from backend.domain.repos.base import CRUDSupported
from backend.internal import Option


class ProfileRepo(CRUDSupported[Profile], Protocol):
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Option[Profile]: ...
