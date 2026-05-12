from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class UpdateNotificationCommand(Command):
    id: UUID
    title: str | None = None
    body: str | None = None
    urgency: int | None = None


@dataclass
class UpdateNotificationHandler(
    Handler[UpdateNotificationCommand, dtos.Notification, None], type_=HandlerType.WRITE
):
    db: Database

    async def __call__(
        self, cmd: UpdateNotificationCommand, _ctx: None = None
    ) -> dtos.Notification:
        async with self.db:
            entity = (await self.db.gateway.notification.get_by_id(cmd.id)).some(NotFoundError())
            if cmd.title is not None:
                entity.title = cmd.title
            if cmd.body is not None:
                entity.body = cmd.body
            if cmd.urgency is not None:
                entity.urgency = cmd.urgency
            updated = (await self.db.gateway.notification.update(entity)).some(NotFoundError())
            await self.db.commit()
        return dtos.Notification.from_object(updated)
