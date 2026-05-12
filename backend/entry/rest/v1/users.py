from uuid import UUID

import msgspec.structs
from litestar import Controller, delete, get, patch, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import users
from backend.app.shared.db.query_services.user import UserWithRoles
from backend.entry.rest.common.response import result
from backend.internal.di import Depends, inject

from .dtos import AssignRoleBody, RevokeRoleBody, UpdateUserBody


class UsersController(Controller):
    path = ""
    tags = ("Users",)

    @get("/users/")
    @inject
    @result
    async def list_users(
        self,
        handler: Depends[users.ListUsersHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.User]:
        return await handler(users.ListUsersCommand(offset=offset, limit=limit))

    @get("/users:listWithRoles", tags=["RBAC"])
    @inject
    @result
    async def list_users_with_roles(
        self,
        handler: Depends[users.ListUsersWithRolesHandler],
        tenant_id: UUID | None = None,
        verified: bool | None = None,  # noqa: FBT001
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[UserWithRoles]:
        return await handler(
            users.ListUsersWithRolesCommand(
                tenant_id=tenant_id,
                verified=verified,
                offset=offset,
                limit=limit,
            )
        )

    @post("/users/")
    @inject
    @result
    async def create_user(
        self,
        data: users.CreateUserCommand,
        handler: Depends[users.CreateUserHandler],
    ) -> dtos.User:
        return await handler(data)

    @get("/users/{id:str}")
    @inject
    @result
    async def get_user(
        self,
        id: str,
        handler: Depends[users.GetUserHandler],
    ) -> dtos.User:
        return await handler(users.GetUserCommand(id=UUID(id)))

    @patch("/users/{id:str}")
    @inject
    @result
    async def update_user(
        self,
        id: str,
        data: UpdateUserBody,
        handler: Depends[users.UpdateUserHandler],
    ) -> dtos.User:
        return await handler(users.UpdateUserCommand(id=UUID(id), **msgspec.structs.asdict(data)))

    @delete("/users/{id:str}")
    @inject
    async def delete_user(
        self,
        id: str,
        handler: Depends[users.DeleteUserHandler],
    ) -> None:
        return await handler(users.DeleteUserCommand(id=UUID(id)))

    @post("/users/{id:str}:assignRole", tags=["RBAC"])
    @inject
    @result
    async def assign_role(
        self,
        id: str,
        data: AssignRoleBody,
        handler: Depends[users.AssignRoleHandler],
    ) -> None:
        return await handler(users.AssignRoleCommand(user_id=UUID(id), role_id=data.role_id))

    @post("/users/{id:str}:revokeRole", tags=["RBAC"])
    @inject
    @result
    async def revoke_role(
        self,
        id: str,
        data: RevokeRoleBody,
        handler: Depends[users.RevokeRoleHandler],
    ) -> None:
        return await handler(users.RevokeRoleCommand(user_id=UUID(id), role_id=data.role_id))
