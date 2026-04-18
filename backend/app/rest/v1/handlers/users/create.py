from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.domain.entities.user import User
from backend.domain.enums import IdentityProvider
from backend.domain.repos.database import Database


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
    db: Database
    identity_service: IdentityService

    async def __call__(self, cmd: CreateUserCommand, _ctx: None = None) -> dtos.User:
        async with self.db:
            entity = User(
                login=cmd.login,
                email=cmd.email,
                first_name=cmd.first_name,
                last_name=cmd.last_name,
                tenant_id=UUID(cmd.tenant_id),
            )
            if cmd.avatar_url is not None:
                entity.avatar_url = cmd.avatar_url
            created = (await self.db.gateway.user.create(entity)).some(AlreadyExistsError())

            await self.identity_service.link_password_identity(
                created.id, IdentityProvider.EMAIL_PASSWORD, cmd.email, cmd.password
            )
            await self.identity_service.link_password_identity(
                created.id, IdentityProvider.USERNAME_PASSWORD, cmd.login, cmd.password
            )

            await self.db.commit()
        return dtos.User.from_object(created)
