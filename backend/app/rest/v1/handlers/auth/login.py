from dataclasses import dataclass

from backend.app.errors import AuthenticationRequiredError
from backend.app.ports.password_hasher import PasswordHasher
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.dtos.auth import AuthContext
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.session import SessionService
from backend.domain.repos.database import Database


class LoginCommand(Command):
    login: str
    password: str


@dataclass
class LoginHandler(Handler[LoginCommand, dtos.User, None], type_=HandlerType.WRITE):
    db: Database
    session_service: SessionService
    password_hasher: PasswordHasher

    async def __call__(self, cmd: LoginCommand, _ctx: None = None) -> AuthContext[dtos.User]:  # type: ignore[override]
        async with self.db:
            user = (await self.db.gateway.user.get_by_login(cmd.login)).some(
                AuthenticationRequiredError(message="Invalid login or password")
            )

            if not self.password_hasher.verify(cmd.password, user.password_hash):
                raise AuthenticationRequiredError(message="Invalid login or password")

            raw_token, _ = await self.session_service.create_session(user.id)

        return AuthContext(token=raw_token, data=dtos.User.from_object(user))
