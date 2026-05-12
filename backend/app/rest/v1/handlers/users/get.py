from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class GetUserCommand(Command):
    id: UUID


@dataclass
class GetUserHandler(Handler[GetUserCommand, dtos.User, None], type_=HandlerType.READ):
    db: Database

    async def __call__(self, cmd: GetUserCommand, _ctx: None = None) -> dtos.User:
        async with self.db:
            user = (await self.db.gateway.user.get_by_id(cmd.id)).some(NotFoundError())
        return dtos.User.from_object(user)
