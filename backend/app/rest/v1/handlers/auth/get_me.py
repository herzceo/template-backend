from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class GetMeCommand(Command):
    user_id: UUID


@dataclass
class GetMeHandler(Handler[GetMeCommand, dtos.User, None], type_=HandlerType.READ):
    db: Database

    async def __call__(self, cmd: GetMeCommand, _ctx: None = None) -> dtos.User:
        async with self.db:
            user = (await self.db.gateway.user.get_by_id(cmd.user_id)).some(
                NotFoundError(message="User not found")
            )
        return dtos.User.from_object(user)
