from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database
from backend.domain.entities.notification import Notification


class CreateNotificationCommand(Command):
    title: str
    body: str
    audience: str
    tenant_id: UUID
    urgency: int = 20
    target_id: UUID | None = None
    sender_id: UUID | None = None


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
                tenant_id=cmd.tenant_id,
                target_id=cmd.target_id,
                sender_id=cmd.sender_id,
            )
            created = (await self.db.gateway.notification.create(entity)).some(AlreadyExistsError())
            await self.db.commit()
        return dtos.Notification.from_object(created)
