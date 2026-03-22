from dataclasses import dataclass

from backend.app.rest.v1.dtos.users import UserShort
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType


class GetUserCommand(Command):
    id: str


@dataclass
class GetUserHandler(Handler[GetUserCommand, UserShort, None], type_=HandlerType.READ):
    async def __call__(self, cmd: GetUserCommand, _ctx: None = None) -> UserShort:
        return UserShort(id=cmd.id)
