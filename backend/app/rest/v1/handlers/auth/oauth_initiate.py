from dataclasses import dataclass

from backend.app.rest.v1.dtos.identity import InitiateResult
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.domain.enums import IdentityProvider


class InitiateOAuthCommand(Command):
    provider: IdentityProvider


@dataclass
class InitiateOAuthHandler(
    Handler[InitiateOAuthCommand, InitiateResult, None],
    type_=HandlerType.READ,
):
    identity_service: IdentityService

    async def __call__(self, cmd: InitiateOAuthCommand, _ctx: None = None) -> InitiateResult:
        return self.identity_service.initiate_oauth(cmd.provider)
