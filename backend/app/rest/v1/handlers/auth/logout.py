from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.session import SessionService


class LogoutCommand(Command):
    session_id: UUID


@dataclass
class LogoutHandler(Handler[LogoutCommand, None, None], type_=HandlerType.WRITE):
    session_service: SessionService

    async def __call__(self, cmd: LogoutCommand, _ctx: None = None) -> None:
        await self.session_service.revoke_session(cmd.session_id)
