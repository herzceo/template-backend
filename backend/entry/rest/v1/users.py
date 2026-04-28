from uuid import UUID

import msgspec.structs
from litestar import Controller, delete, get, patch, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import users
from backend.entry.rest.common.response import result
from backend.internal.di import Depends, inject

from .dtos import UpdateUserBody


class UsersController(Controller):
    path = "/users"
    tags = ("Users",)

    @get("/")
    @inject
    @result
    async def list_users(
        self,
        handler: Depends[users.ListUsersHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.User]:
        return await handler(users.ListUsersCommand(offset=offset, limit=limit))

    @post("/")
    @inject
    @result
    async def create_user(
        self,
        data: users.CreateUserCommand,
        handler: Depends[users.CreateUserHandler],
    ) -> dtos.User:
        return await handler(data)

    @get("/{id:str}")
    @inject
    @result
    async def get_user(
        self,
        id: str,
        handler: Depends[users.GetUserHandler],
    ) -> dtos.User:
        return await handler(users.GetUserCommand(id=UUID(id)))

    @patch("/{id:str}")
    @inject
    @result
    async def update_user(
        self,
        id: str,
        data: UpdateUserBody,
        handler: Depends[users.UpdateUserHandler],
    ) -> dtos.User:
        return await handler(users.UpdateUserCommand(id=UUID(id), **msgspec.structs.asdict(data)))

    @delete("/{id:str}")
    @inject
    @result
    async def delete_user(
        self,
        id: str,
        handler: Depends[users.DeleteUserHandler],
    ) -> None:
        return await handler(users.DeleteUserCommand(id=UUID(id)))

    @post("/{id:str}/roles/{role_id:str}", tags=["RBAC"])
    @inject
    @result
    async def assign_role(
        self,
        id: str,
        role_id: str,
        handler: Depends[users.AssignRoleHandler],
    ) -> None:
        return await handler(users.AssignRoleCommand(user_id=UUID(id), role_id=UUID(role_id)))

    @delete("/{id:str}/roles/{role_id:str}", tags=["RBAC"])
    @inject
    @result
    async def revoke_role(
        self,
        id: str,
        role_id: str,
        handler: Depends[users.RevokeRoleHandler],
    ) -> None:
        return await handler(users.RevokeRoleCommand(user_id=UUID(id), role_id=UUID(role_id)))
