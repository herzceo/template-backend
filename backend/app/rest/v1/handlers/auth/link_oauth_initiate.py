from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.dtos.identity import InitiateResult
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.domain.enums import IdentityProvider


class LinkOAuthInitiateCommand(Command):
    user_id: UUID
    provider: IdentityProvider
    redirect_uri: str


@dataclass
class LinkOAuthInitiateHandler(
    Handler[LinkOAuthInitiateCommand, InitiateResult, None], type_=HandlerType.READ
):
    identity_service: IdentityService

    async def __call__(self, cmd: LinkOAuthInitiateCommand, _ctx: None = None) -> InitiateResult:
        return self.identity_service.initiate_link(cmd.provider, cmd.redirect_uri, cmd.user_id)
