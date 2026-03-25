from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class MarkReadCommand(Command):
    notification_id: str
    user_id: str


@dataclass
class MarkReadHandler(Handler[MarkReadCommand, None, None], type_=HandlerType.WRITE):
    gateway: RepoGateway

    async def __call__(self, cmd: MarkReadCommand, _ctx: None = None) -> None:
        await self.gateway.notification.mark_read(UUID(cmd.notification_id), UUID(cmd.user_id))
        await self.gateway.commiter.commit()
