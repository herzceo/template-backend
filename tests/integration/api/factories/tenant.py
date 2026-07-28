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
    is_default: bool = False,
) -> Tenant:
    # Default is_default=False: the session-scoped DB accumulates every tenant a
    # test creates, and `tenant.get_default()` uses `scalar_one_or_none` — so more
    # than one default tenant would make it raise. Exactly one default is seeded on
    # demand via `ensure_default_tenant` (used by the OAuth signup path).
    async with container() as c:
        db: Database = await c.get(Database)
        async with db:
            tenant = Tenant(
                id=uuid4(),
                name=name,
                slug=slug or f"test-{uuid4().hex[:8]}",
                is_default=is_default,
            )
            created = (await db.gateway.tenant.create(tenant)).some(
                RuntimeError("Failed to create tenant")
            )
            await db.commit()
    return created


async def ensure_default_tenant(container: AsyncContainer) -> Tenant:
    """Return the one default tenant, creating it if none exists yet.

    Idempotent, so the OAuth signup flow (which resolves the default tenant) works
    no matter how many tests have run before it, without ever minting a second
    default row.
    """
    async with container() as c:
        db: Database = await c.get(Database)
        async with db:
            existing = (await db.gateway.tenant.get_default()).value
            if existing is not None:
                return existing
            tenant = Tenant(
                id=uuid4(),
                name="Default Tenant",
                slug=f"default-{uuid4().hex[:8]}",
                is_default=True,
            )
            created = (await db.gateway.tenant.create(tenant)).some(
                RuntimeError("Failed to create default tenant")
            )
            await db.commit()
    return created
