from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.entities.user import User
from backend.domain.repos.gateway import RepoGateway


class CreateUserCommand(Command):
    login: str
    email: str
    password: str
    first_name: str
    last_name: str
    tenant_id: str
    avatar_url: str | None = None


@dataclass
class CreateUserHandler(Handler[CreateUserCommand, dtos.User, None], type_=HandlerType.WRITE):
    gateway: RepoGateway

    async def __call__(self, cmd: CreateUserCommand, _ctx: None = None) -> dtos.User:
        entity = User(
            login=cmd.login,
            email=cmd.email,
            password_hash=cmd.password,
            first_name=cmd.first_name,
            last_name=cmd.last_name,
            tenant_id=UUID(cmd.tenant_id),
        )
        if cmd.avatar_url is not None:
            entity.avatar_url = cmd.avatar_url
        created = (await self.gateway.user.create(entity)).some(AlreadyExistsError())
        await self.gateway.commiter.commit()
        return dtos.User.from_object(created)
