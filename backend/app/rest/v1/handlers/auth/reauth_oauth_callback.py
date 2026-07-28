from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import AuthenticationRequiredError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.auth.reauth_password import REAUTH_TOKEN_TTL_SECONDS
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.shared.db.database import Database
from backend.app.shared.ports.security.one_time_token import (
    OTT_PURPOSE_REAUTH,
    OneTimeTokenStore,
)
from backend.domain.enums import IdentityProvider


class ReauthOAuthCallbackCommand(Command):
    user_id: UUID
    provider: IdentityProvider
    code: str
    state: str
    redirect_uri: str


@dataclass
class ReauthOAuthCallbackHandler(
    Handler[ReauthOAuthCallbackCommand, dtos.ReauthToken, None], type_=HandlerType.WRITE
):
    db: Database
    identity_service: IdentityService
    ott_store: OneTimeTokenStore

    async def __call__(
        self, cmd: ReauthOAuthCallbackCommand, _ctx: None = None
    ) -> dtos.ReauthToken:
        async with self.db:
            ok = await self.identity_service.verify_reauth(
                cmd.provider, cmd.code, cmd.state, cmd.redirect_uri, cmd.user_id
            )
        if not ok:
            raise AuthenticationRequiredError(
                message="That account isn't linked to you — re-authentication failed"
            )
        token = await self.ott_store.issue(
            OTT_PURPOSE_REAUTH, cmd.user_id, REAUTH_TOKEN_TTL_SECONDS
        )
        return dtos.ReauthToken(reauth_token=token)
