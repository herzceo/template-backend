from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.validation import normalize_email, normalize_username
from backend.domain.entities.profile import Profile
from backend.domain.entities.user import User
from backend.domain.enums import IdentityProvider
from backend.domain.repos.database import Database


class CreateUserCommand(Command):
    username: str
    email: str
    password: str
    tenant_id: UUID


@dataclass
class CreateUserHandler(Handler[CreateUserCommand, dtos.User, None], type_=HandlerType.WRITE):
    db: Database
    identity_service: IdentityService

    async def __call__(self, cmd: CreateUserCommand, _ctx: None = None) -> dtos.User:
        username = normalize_username(cmd.username)
        email = normalize_email(cmd.email)

        async with self.db:
            entity = User(
                username=username,
                email=email,
                tenant_id=cmd.tenant_id,
            )
            created = (await self.db.gateway.user.create(entity)).some(AlreadyExistsError())

            profile = Profile(user_id=created.id)
            (await self.db.gateway.profile.create(profile)).some(
                RuntimeError("Failed to create profile")
            )

            await self.identity_service.link_password_identity(
                created.id, IdentityProvider.EMAIL_PASSWORD, email, cmd.password
            )
            await self.identity_service.link_password_identity(
                created.id, IdentityProvider.USERNAME_PASSWORD, username, cmd.password
            )

            await self.db.commit()
        return dtos.User.from_object(created)
