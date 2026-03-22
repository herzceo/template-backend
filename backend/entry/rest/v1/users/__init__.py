from litestar import Controller, get

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import users


class UsersController(Controller):
    path = "/users"

    @get("/{id}")
    async def get_user(self, id: str, handler: users.GetUserHandler) -> dtos.UserShort:
        return await handler(users.GetUserCommand(id=id))
