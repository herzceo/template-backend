from dataclasses import dataclass

from backend.app.rest.v1.dtos.identity import InitiateResult
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.domain.enums import IdentityProvider


class InitiateOAuthCommand(Command):
    provider: IdentityProvider
    # Same-origin callback on the frontend host that initiated the flow. Built by
    # the controller from the request host so the browser always returns to the
    # front end and the session cookie is set on that host.
    redirect_uri: str


@dataclass
class InitiateOAuthHandler(
    Handler[InitiateOAuthCommand, InitiateResult, None],
    type_=HandlerType.READ,
):
    identity_service: IdentityService

    async def __call__(self, cmd: InitiateOAuthCommand, _ctx: None = None) -> InitiateResult:
        return self.identity_service.initiate_oauth(cmd.provider, cmd.redirect_uri)
