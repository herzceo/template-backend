from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.domain.entities.role import Role
from backend.domain.entities.user import User
from backend.domain.repos.base import CRUDSupported
from backend.internal import Option


class UserRepo(CRUDSupported[User], Protocol):
    @abstractmethod
    async def get_by_login(self, login: str) -> Option[User]: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Option[User]: ...

    @abstractmethod
    async def assign_role(self, user_id: UUID, role_id: UUID) -> None: ...

    @abstractmethod
    async def revoke_role(self, user_id: UUID, role_id: UUID) -> None: ...

    @abstractmethod
    async def get_roles(self, user_id: UUID) -> list[Role]: ...
