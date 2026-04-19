from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.ports.dbus import DBus
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.shared.events.v1.user_verification_requested import UserVerificationRequested
from backend.domain.entities.user import User
from backend.domain.enums import IdentityProvider
from backend.domain.repos.database import Database


class SignupCommand(Command):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    tenant_id: UUID


@dataclass
class SignupHandler(Handler[SignupCommand, dtos.User, None], type_=HandlerType.WRITE):
    db: Database
    identity_service: IdentityService
    dbus: DBus

    async def __call__(self, cmd: SignupCommand, _ctx: None = None) -> dtos.User:
        async with self.db:
            entity = User(
                username=cmd.username,
                email=cmd.email,
                first_name=cmd.first_name,
                last_name=cmd.last_name,
                tenant_id=cmd.tenant_id,
            )
            created = (await self.db.gateway.user.create(entity)).some(AlreadyExistsError())

            await self.identity_service.link_password_identity(
                created.id, IdentityProvider.EMAIL_PASSWORD, cmd.email, cmd.password
            )
            await self.identity_service.link_password_identity(
                created.id, IdentityProvider.USERNAME_PASSWORD, cmd.username, cmd.password
            )

            await self.dbus.publish(
                UserVerificationRequested(
                    user_id=created.id,
                    email=cmd.email,
                    username=cmd.username,
                )
            )

            await self.db.commit()

        return dtos.User.from_object(created)
