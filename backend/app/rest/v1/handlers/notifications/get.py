from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class GetNotificationCommand(Command):
    id: str


@dataclass
class GetNotificationHandler(
    Handler[GetNotificationCommand, dtos.Notification, None], type_=HandlerType.READ
):
    gateway: RepoGateway

    async def __call__(self, cmd: GetNotificationCommand, _ctx: None = None) -> dtos.Notification:
        notification = (await self.gateway.notification.get_by_id(UUID(cmd.id))).some(
            NotFoundError()
        )
        return dtos.Notification.from_object(notification)
