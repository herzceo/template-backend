from uuid import UUID

import msgspec.structs
from litestar import Controller, delete, get, patch, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import permissions
from backend.internal.di import Depends

from .dtos import UpdatePermissionBody


class PermissionsController(Controller):
    path = "/permissions"
    tags = (
        "Permissions",
        "RBAC",
    )

    @get("/")
    async def list_permissions(
        self,
        handler: Depends[permissions.ListPermissionsHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.Permission]:
        return await handler(permissions.ListPermissionsCommand(offset=offset, limit=limit))

    @post("/")
    async def create_permission(
        self,
        data: permissions.CreatePermissionCommand,
        handler: Depends[permissions.CreatePermissionHandler],
    ) -> dtos.Permission:
        return await handler(data)

    @get("/{id:str}")
    async def get_permission(
        self,
        id: str,
        handler: Depends[permissions.GetPermissionHandler],
    ) -> dtos.Permission:
        return await handler(permissions.GetPermissionCommand(id=UUID(id)))

    @patch("/{id:str}")
    async def update_permission(
        self,
        id: str,
        data: UpdatePermissionBody,
        handler: Depends[permissions.UpdatePermissionHandler],
    ) -> dtos.Permission:
        return await handler(
            permissions.UpdatePermissionCommand(id=UUID(id), **msgspec.structs.asdict(data))
        )

    @delete("/{id:str}")
    async def delete_permission(
        self,
        id: str,
        handler: Depends[permissions.DeletePermissionHandler],
    ) -> None:
        return await handler(permissions.DeletePermissionCommand(id=UUID(id)))
