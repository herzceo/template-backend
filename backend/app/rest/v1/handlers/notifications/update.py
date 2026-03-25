from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class UpdateNotificationCommand(Command):
    id: str
    title: str | None = None
    body: str | None = None
    urgency: int | None = None


@dataclass
class UpdateNotificationHandler(
    Handler[UpdateNotificationCommand, dtos.Notification, None], type_=HandlerType.WRITE
):
    gateway: RepoGateway

    async def __call__(
        self, cmd: UpdateNotificationCommand, _ctx: None = None
    ) -> dtos.Notification:
        entity = (await self.gateway.notification.get_by_id(UUID(cmd.id))).some(NotFoundError())
        if cmd.title is not None:
            entity.title = cmd.title
        if cmd.body is not None:
            entity.body = cmd.body
        if cmd.urgency is not None:
            entity.urgency = cmd.urgency
        updated = (await self.gateway.notification.update(entity)).some(NotFoundError())
        await self.gateway.commiter.commit()
        return dtos.Notification.from_object(updated)
