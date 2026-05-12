from typing import Any
from uuid import UUID

from dishka.integrations.litestar import FromDishka
from litestar.connection import Request
from litestar.exceptions import InternalServerException, NotFoundException

from backend.app.shared.db.database import Database


async def resolve_tenant_id(request: Request[Any, Any, Any], db: FromDishka[Database]) -> UUID:
    app_id = request.headers.get("X-App-Id")
    async with db:
        if app_id is not None:
            tenant = (await db.gateway.tenant.get_by_app_id(app_id)).some(
                NotFoundException(detail=f"Tenant '{app_id}' not found")
            )
        else:
            tenant = (await db.gateway.tenant.get_default()).some(
                InternalServerException(detail="No default tenant configured")
            )
    return tenant.id
