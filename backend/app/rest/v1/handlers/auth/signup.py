from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.validation import normalize_email, normalize_username
from backend.app.shared.db.database import Database
from backend.app.shared.events.v1.user_verification_requested import UserVerificationRequested
from backend.domain.entities.profile import Profile
from backend.domain.entities.user import User
from backend.domain.enums import IdentityProvider


class SignupCommand(Command):
    username: str
    email: str
    password: str
    tenant_id: UUID


@dataclass
class SignupHandler(Handler[SignupCommand, dtos.User, None], type_=HandlerType.WRITE):
    db: Database
    identity_service: IdentityService

    async def __call__(self, cmd: SignupCommand, _ctx: None = None) -> dtos.User:
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

            await self.db.dbus.publish(
                UserVerificationRequested(
                    user_id=created.id,
                    email=email,
                    username=username,
                )
            )

            await self.db.commit()

        return dtos.User.from_object(created)
