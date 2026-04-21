from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class DismissCommand(Command):
    notification_id: UUID
    user_id: UUID


@dataclass
class DismissHandler(Handler[DismissCommand, None, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: DismissCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.notification.mark_dismissed(cmd.notification_id, cmd.user_id)
            await self.db.commit()
