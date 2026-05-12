from dataclasses import dataclass

from backend.app.errors import AuthenticationRequiredError, ValidationFailedError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.dtos.auth import AuthContext
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.services.session import SessionService
from backend.app.rest.v1.services.types import ClientDeviceInfo
from backend.app.shared.db.database import Database
from backend.domain.enums import IdentityProvider


class LoginCommand(Command):
    username: str
    password: str
    ip: str | None = None
    user_agent: str | None = None
    client_device: ClientDeviceInfo | None = None


@dataclass
class LoginHandler(Handler[LoginCommand, AuthContext[dtos.User], None], type_=HandlerType.WRITE):
    db: Database
    session_service: SessionService
    identity_service: IdentityService

    async def __call__(self, cmd: LoginCommand, _ctx: None = None) -> AuthContext[dtos.User]:
        provider = (
            IdentityProvider.EMAIL_PASSWORD
            if "@" in cmd.username
            else IdentityProvider.USERNAME_PASSWORD
        )
        async with self.db:
            identity = await self.identity_service.verify_password(
                provider, cmd.username, cmd.password
            )
            user = (await self.db.gateway.user.get_by_id(identity.user_id)).some(
                AuthenticationRequiredError(message="User not found")
            )
            if not user.is_verified:
                raise ValidationFailedError(message="Email not verified")
            user_id = user.id
            await self.db.commit()
        raw_token, _ = await self.session_service.create_session(
            user_id,
            ip=cmd.ip,
            user_agent=cmd.user_agent,
            client_device=cmd.client_device,
        )
        return AuthContext(token=raw_token, data=dtos.User.from_object(user))
