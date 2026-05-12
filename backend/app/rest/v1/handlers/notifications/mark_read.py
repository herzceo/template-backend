from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class MarkReadCommand(Command):
    notification_id: UUID
    user_id: UUID


@dataclass
class MarkReadHandler(Handler[MarkReadCommand, None, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: MarkReadCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.notification.mark_read(cmd.notification_id, cmd.user_id)
            await self.db.commit()
