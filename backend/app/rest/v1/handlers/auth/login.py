from dataclasses import dataclass

from backend.app.errors import AuthenticationRequiredError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.dtos.auth import AuthContext
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.services.session import SessionService
from backend.domain.enums import IdentityProvider
from backend.domain.repos.database import Database


class LoginCommand(Command):
    login: str
    password: str


@dataclass
class LoginHandler(Handler[LoginCommand, AuthContext[dtos.User], None], type_=HandlerType.WRITE):
    db: Database
    session_service: SessionService
    identity_service: IdentityService

    async def __call__(self, cmd: LoginCommand, _ctx: None = None) -> AuthContext[dtos.User]:
        async with self.db:
            provider = (
                IdentityProvider.EMAIL_PASSWORD
                if "@" in cmd.login
                else IdentityProvider.USERNAME_PASSWORD
            )
            identity = await self.identity_service.verify_password(
                provider, cmd.login, cmd.password
            )
            user = (await self.db.gateway.user.get_by_id(identity.user_id)).some(
                AuthenticationRequiredError(message="User not found")
            )
            raw_token, _ = await self.session_service.create_session(user.id)

        return AuthContext(token=raw_token, data=dtos.User.from_object(user))
