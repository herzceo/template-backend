from uuid import UUID

import msgspec.structs
from litestar import Controller, delete, get, patch, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import roles
from backend.entry.rest.common.response import result
from backend.internal.di import Depends, inject

from .dtos import AssignPermissionBody, RevokePermissionBody, UpdateRoleBody


class RolesController(Controller):
    path = ""
    tags = (
        "Roles",
        "RBAC",
    )

    @get("/roles/")
    @inject
    @result
    async def list_roles(
        self,
        handler: Depends[roles.ListRolesHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.Role]:
        return await handler(roles.ListRolesCommand(offset=offset, limit=limit))

    @post("/roles/")
    @inject
    @result
    async def create_role(
        self,
        data: roles.CreateRoleCommand,
        handler: Depends[roles.CreateRoleHandler],
    ) -> dtos.Role:
        return await handler(data)

    @get("/roles/{id:uuid}")
    @inject
    @result
    async def get_role(
        self,
        id: UUID,
        handler: Depends[roles.GetRoleHandler],
    ) -> dtos.Role:
        return await handler(roles.GetRoleCommand(id=id))

    @patch("/roles/{id:uuid}")
    @inject
    @result
    async def update_role(
        self,
        id: UUID,
        data: UpdateRoleBody,
        handler: Depends[roles.UpdateRoleHandler],
    ) -> dtos.Role:
        return await handler(roles.UpdateRoleCommand(id=id, **msgspec.structs.asdict(data)))

    @delete("/roles/{id:uuid}")
    @inject
    async def delete_role(
        self,
        id: UUID,
        handler: Depends[roles.DeleteRoleHandler],
    ) -> None:
        return await handler(roles.DeleteRoleCommand(id=id))

    @post("/roles/assignPermission")
    @inject
    @result
    async def assign_permission(
        self,
        data: AssignPermissionBody,
        handler: Depends[roles.AssignPermissionHandler],
    ) -> None:
        return await handler(
            roles.AssignPermissionCommand(role_id=data.role_id, permission_id=data.permission_id)
        )

    @post("/roles/revokePermission")
    @inject
    @result
    async def revoke_permission(
        self,
        data: RevokePermissionBody,
        handler: Depends[roles.RevokePermissionHandler],
    ) -> None:
        return await handler(
            roles.RevokePermissionCommand(role_id=data.role_id, permission_id=data.permission_id)
        )
