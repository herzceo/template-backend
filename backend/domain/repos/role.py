from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.domain.entities.permission import Permission
from backend.domain.entities.role import Role
from backend.domain.repos.base import CRUDSupported


class RoleRepo(CRUDSupported[Role], Protocol):
    @abstractmethod
    async def assign_permission(self, role_id: UUID, permission_id: UUID) -> None: ...

    @abstractmethod
    async def revoke_permission(self, role_id: UUID, permission_id: UUID) -> None: ...

    @abstractmethod
    async def get_permissions(self, role_id: UUID) -> list[Permission]: ...
