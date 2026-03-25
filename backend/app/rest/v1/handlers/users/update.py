from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class UpdateUserCommand(Command):
    id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None


@dataclass
class UpdateUserHandler(Handler[UpdateUserCommand, dtos.User, None], type_=HandlerType.WRITE):
    gateway: RepoGateway

    async def __call__(self, cmd: UpdateUserCommand, _ctx: None = None) -> dtos.User:
        entity = (await self.gateway.user.get_by_id(UUID(cmd.id))).some(NotFoundError())
        if cmd.email is not None:
            entity.email = cmd.email
        if cmd.first_name is not None:
            entity.first_name = cmd.first_name
        if cmd.last_name is not None:
            entity.last_name = cmd.last_name
        if cmd.avatar_url is not None:
            entity.avatar_url = cmd.avatar_url
        updated = (await self.gateway.user.update(entity)).some(NotFoundError())
        await self.gateway.commiter.commit()
        return dtos.User.from_object(updated)
