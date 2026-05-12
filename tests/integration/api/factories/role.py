from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from backend.app.shared.db.database import Database
from backend.domain.entities.permission import Permission
from backend.domain.entities.role import Role

if TYPE_CHECKING:
    from dishka import AsyncContainer


async def create_role(
    container: AsyncContainer,
    tenant_id: UUID,
    *,
    name: str | None = None,
    description: str = "Test role",
) -> Role:
    async with container() as c:
        db: Database = await c.get(Database)
        async with db:
            role = Role(
                id=uuid4(),
                name=name or f"role_{uuid4().hex[:8]}",
                description=description,
                tenant_id=tenant_id,
            )
            created = (await db.gateway.role.create(role)).some(
                RuntimeError("Failed to create role")
            )
            await db.commit()
    return created


async def create_permission(
    container: AsyncContainer,
    *,
    codename: str | None = None,
    description: str = "Test permission",
) -> Permission:
    async with container() as c:
        db: Database = await c.get(Database)
        async with db:
            permission = Permission(
                id=uuid4(),
                codename=codename or f"perm:{uuid4().hex[:8]}",
                description=description,
            )
            created = (await db.gateway.permission.create(permission)).some(
                RuntimeError("Failed to create permission")
            )
            await db.commit()
    return created
