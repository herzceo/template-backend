from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.shared.db.database import Database
from backend.app.shared.events.v1.oauth_identity_attached import OAuthIdentityAttached
from backend.domain.enums import IdentityProvider


class LinkOAuthCallbackCommand(Command):
    user_id: UUID
    provider: IdentityProvider
    code: str
    state: str
    redirect_uri: str


@dataclass
class LinkOAuthCallbackHandler(
    Handler[LinkOAuthCallbackCommand, None, None], type_=HandlerType.WRITE
):
    """Link the returned provider identity to the CURRENT user (no session change).

    Errors (``provider_already_linked``) when the identity belongs to someone
    else — never logs the user into that other account.
    """

    db: Database
    identity_service: IdentityService

    async def __call__(self, cmd: LinkOAuthCallbackCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.identity_service.link_oauth_to_user(
                cmd.provider, cmd.code, cmd.state, cmd.redirect_uri, cmd.user_id
            )
            user = (await self.db.gateway.user.get_by_id(cmd.user_id)).value
            if user is not None:
                await self.db.dbus.publish(
                    OAuthIdentityAttached(
                        user_id=cmd.user_id,
                        email=user.email,
                        username=user.username,
                        provider=cmd.provider.value,
                    )
                )
            await self.db.commit()
