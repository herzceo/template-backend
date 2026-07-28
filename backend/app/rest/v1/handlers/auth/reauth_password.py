from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import AuthenticationRequiredError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.shared.db.database import Database
from backend.app.shared.ports.security.one_time_token import (
    OTT_PURPOSE_REAUTH,
    OneTimeTokenStore,
)

# Step-up proof lifetime — long enough to complete a two-step change, short enough
# that a stolen token has little value.
REAUTH_TOKEN_TTL_SECONDS = 10 * 60


class ReauthPasswordCommand(Command):
    user_id: UUID
    password: str


@dataclass
class ReauthPasswordHandler(
    Handler[ReauthPasswordCommand, dtos.ReauthToken, None], type_=HandlerType.WRITE
):
    db: Database
    identity_service: IdentityService
    ott_store: OneTimeTokenStore

    async def __call__(self, cmd: ReauthPasswordCommand, _ctx: None = None) -> dtos.ReauthToken:
        async with self.db:
            ok = await self.identity_service.verify_user_password(cmd.user_id, cmd.password)
        if not ok:
            raise AuthenticationRequiredError(message="Incorrect password")
        token = await self.ott_store.issue(
            OTT_PURPOSE_REAUTH, cmd.user_id, REAUTH_TOKEN_TTL_SECONDS
        )
        return dtos.ReauthToken(reauth_token=token)
