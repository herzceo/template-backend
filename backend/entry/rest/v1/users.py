import msgspec.structs
from litestar import Controller, delete, get, patch, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import users
from backend.internal.di import Depends, inject

from .dtos import UpdateUserBody


class UsersController(Controller):
    path = "/users"
    tags = ("Users",)

    @get("/")
    @inject
    async def list_users(
        self,
        handler: Depends[users.ListUsersHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.User]:
        return await handler(users.ListUsersCommand(offset=offset, limit=limit))

    @post("/")
    @inject
    async def create_user(
        self,
        data: users.CreateUserCommand,
        handler: Depends[users.CreateUserHandler],
    ) -> dtos.User:
        return await handler(data)

    @get("/{id:str}")
    @inject
    async def get_user(
        self,
        id: str,
        handler: Depends[users.GetUserHandler],
    ) -> dtos.User:
        return await handler(users.GetUserCommand(id=id))

    @patch("/{id:str}")
    @inject
    async def update_user(
        self,
        id: str,
        data: UpdateUserBody,
        handler: Depends[users.UpdateUserHandler],
    ) -> dtos.User:
        return await handler(users.UpdateUserCommand(id=id, **msgspec.structs.asdict(data)))

    @delete("/{id:str}")
    @inject
    async def delete_user(
        self,
        id: str,
        handler: Depends[users.DeleteUserHandler],
    ) -> None:
        return await handler(users.DeleteUserCommand(id=id))

    @post("/{id:str}/roles/{role_id:str}", tags=["RBAC"])
    @inject
    async def assign_role(
        self,
        id: str,
        role_id: str,
        handler: Depends[users.AssignRoleHandler],
    ) -> None:
        return await handler(users.AssignRoleCommand(user_id=id, role_id=role_id))

    @delete("/{id:str}/roles/{role_id:str}", tags=["RBAC"])
    @inject
    async def revoke_role(
        self,
        id: str,
        role_id: str,
        handler: Depends[users.RevokeRoleHandler],
    ) -> None:
        return await handler(users.RevokeRoleCommand(user_id=id, role_id=role_id))
