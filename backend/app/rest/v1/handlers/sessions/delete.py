from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class DeleteSessionCommand(Command):
    id: UUID


@dataclass
class DeleteSessionHandler(Handler[DeleteSessionCommand, None, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: DeleteSessionCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.session_.delete_by_id(cmd.id)
            await self.db.commit()
