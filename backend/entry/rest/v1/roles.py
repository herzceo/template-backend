from uuid import UUID

import msgspec.structs
from litestar import Controller, delete, get, patch, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import roles
from backend.entry.rest.common.response import result
from backend.internal.di import Depends, inject

from .dtos import AssignPermissionBody, RevokePermissionBody, UpdateRoleBody


class RolesController(Controller):
    path = "/roles"
    tags = (
        "Roles",
        "RBAC",
    )

    @get("/")
    @inject
    @result
    async def list_roles(
        self,
        handler: Depends[roles.ListRolesHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.Role]:
        return await handler(roles.ListRolesCommand(offset=offset, limit=limit))

    @post("/")
    @inject
    @result
    async def create_role(
        self,
        data: roles.CreateRoleCommand,
        handler: Depends[roles.CreateRoleHandler],
    ) -> dtos.Role:
        return await handler(data)

    @get("/{id:str}")
    @inject
    @result
    async def get_role(
        self,
        id: str,
        handler: Depends[roles.GetRoleHandler],
    ) -> dtos.Role:
        return await handler(roles.GetRoleCommand(id=UUID(id)))

    @patch("/{id:str}")
    @inject
    @result
    async def update_role(
        self,
        id: str,
        data: UpdateRoleBody,
        handler: Depends[roles.UpdateRoleHandler],
    ) -> dtos.Role:
        return await handler(roles.UpdateRoleCommand(id=UUID(id), **msgspec.structs.asdict(data)))

    @delete("/{id:str}")
    @inject
    async def delete_role(
        self,
        id: str,
        handler: Depends[roles.DeleteRoleHandler],
    ) -> None:
        return await handler(roles.DeleteRoleCommand(id=UUID(id)))

    @post("/{id:str}:assignPermission")
    @inject
    @result
    async def assign_permission(
        self,
        id: str,
        data: AssignPermissionBody,
        handler: Depends[roles.AssignPermissionHandler],
    ) -> None:
        return await handler(
            roles.AssignPermissionCommand(role_id=UUID(id), permission_id=data.permission_id)
        )

    @post("/{id:str}:revokePermission")
    @inject
    @result
    async def revoke_permission(
        self,
        id: str,
        data: RevokePermissionBody,
        handler: Depends[roles.RevokePermissionHandler],
    ) -> None:
        return await handler(
            roles.RevokePermissionCommand(role_id=UUID(id), permission_id=data.permission_id)
        )
