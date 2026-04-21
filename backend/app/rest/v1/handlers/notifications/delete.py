from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class DeleteNotificationCommand(Command):
    id: UUID


@dataclass
class DeleteNotificationHandler(
    Handler[DeleteNotificationCommand, None, None], type_=HandlerType.WRITE
):
    db: Database

    async def __call__(self, cmd: DeleteNotificationCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.notification.delete_by_id(cmd.id)
            await self.db.commit()
