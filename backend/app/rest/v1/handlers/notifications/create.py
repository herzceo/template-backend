from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.entities.notification import Notification
from backend.domain.repos.database import Database


class CreateNotificationCommand(Command):
    title: str
    body: str
    audience: str
    tenant_id: str
    urgency: int = 20
    target_id: str | None = None
    sender_id: str | None = None


@dataclass
class CreateNotificationHandler(
    Handler[CreateNotificationCommand, dtos.Notification, None], type_=HandlerType.WRITE
):
    db: Database

    async def __call__(
        self, cmd: CreateNotificationCommand, _ctx: None = None
    ) -> dtos.Notification:
        async with self.db:
            entity = Notification(
                title=cmd.title,
                body=cmd.body,
                audience=cmd.audience,
                urgency=cmd.urgency,
                tenant_id=UUID(cmd.tenant_id),
                target_id=UUID(cmd.target_id) if cmd.target_id else None,
                sender_id=UUID(cmd.sender_id) if cmd.sender_id else None,
            )
            created = (await self.db.gateway.notification.create(entity)).some(AlreadyExistsError())
            await self.db.commit()
        return dtos.Notification.from_object(created)
