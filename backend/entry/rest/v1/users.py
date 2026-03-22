from litestar import Controller, get

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import users
from backend.internal.di import Depends, inject


class UsersController(Controller):
    path = "/users"

    @get("/{id:str}")
    @inject
    async def get_user(self, id: str, handler: Depends[users.GetUserHandler]) -> dtos.UserShort:
        return await handler(users.GetUserCommand(id=id))
