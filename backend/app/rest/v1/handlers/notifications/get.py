from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class GetNotificationCommand(Command):
    id: UUID


@dataclass
class GetNotificationHandler(
    Handler[GetNotificationCommand, dtos.Notification, None], type_=HandlerType.READ
):
    db: Database

    async def __call__(self, cmd: GetNotificationCommand, _ctx: None = None) -> dtos.Notification:
        async with self.db:
            notification = (await self.db.gateway.notification.get_by_id(cmd.id)).some(
                NotFoundError()
            )
            return dtos.Notification.from_object(notification)
