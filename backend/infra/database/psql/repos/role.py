from typing import final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.domain.entities.permission import Permission
from backend.domain.entities.role import Role
from backend.domain.repos.role import RoleRepo

from .base import ImplCRUDSupported


@final
class ImplRoleRepo(ImplCRUDSupported[Role], RoleRepo):
    __slots__ = ()

    async def assign_permission(self, role_id: UUID, permission_id: UUID) -> None:
        stmt = select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        result = await self._session.execute(stmt)
        role = result.scalar_one()
        permission = await self._session.get_one(Permission, permission_id)
        role.permissions.append(permission)

    async def revoke_permission(self, role_id: UUID, permission_id: UUID) -> None:
        stmt = select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        result = await self._session.execute(stmt)
        role = result.scalar_one()
        permission = await self._session.get_one(Permission, permission_id)
        role.permissions.remove(permission)

    async def get_permissions(self, role_id: UUID) -> list[Permission]:
        stmt = select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        result = await self._session.execute(stmt)
        role = result.scalar_one()
        return list(role.permissions)
