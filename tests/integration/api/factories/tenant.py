from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from backend.app.shared.db.database import Database
from backend.domain.entities.tenant import Tenant

if TYPE_CHECKING:
    from dishka import AsyncContainer


async def create_tenant(
    container: AsyncContainer,
    *,
    name: str = "Test Tenant",
    slug: str | None = None,
    is_default: bool = True,
    app_id: str | None = None,
) -> Tenant:
    async with container() as c:
        db: Database = await c.get(Database)
        async with db:
            tenant = Tenant(
                id=uuid4(),
                name=name,
                slug=slug or f"test-{uuid4().hex[:8]}",
                is_default=is_default,
                app_id=app_id,
            )
            created = (await db.gateway.tenant.create(tenant)).some(
                RuntimeError("Failed to create tenant")
            )
            await db.commit()
    return created
