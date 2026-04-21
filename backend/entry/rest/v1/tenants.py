from uuid import UUID

import msgspec.structs
from litestar import Controller, delete, get, patch, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import tenants
from backend.internal.di import Depends, inject

from .dtos import UpdateTenantBody


class TenantsController(Controller):
    path = "/tenants"
    tags = ("Tenants",)

    @get("/")
    @inject
    async def list_tenants(
        self,
        handler: Depends[tenants.ListTenantsHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.Tenant]:
        return await handler(tenants.ListTenantsCommand(offset=offset, limit=limit))

    @post("/")
    @inject
    async def create_tenant(
        self,
        data: tenants.CreateTenantCommand,
        handler: Depends[tenants.CreateTenantHandler],
    ) -> dtos.Tenant:
        return await handler(data)

    @get("/{id:str}")
    @inject
    async def get_tenant(
        self,
        id: str,
        handler: Depends[tenants.GetTenantHandler],
    ) -> dtos.Tenant:
        return await handler(tenants.GetTenantCommand(id=UUID(id)))

    @patch("/{id:str}")
    @inject
    async def update_tenant(
        self,
        id: str,
        data: UpdateTenantBody,
        handler: Depends[tenants.UpdateTenantHandler],
    ) -> dtos.Tenant:
        return await handler(
            tenants.UpdateTenantCommand(id=UUID(id), **msgspec.structs.asdict(data))
        )

    @delete("/{id:str}")
    @inject
    async def delete_tenant(
        self,
        id: str,
        handler: Depends[tenants.DeleteTenantHandler],
    ) -> None:
        return await handler(tenants.DeleteTenantCommand(id=UUID(id)))
