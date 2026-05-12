from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class DeletePermissionCommand(Command):
    id: UUID


@dataclass
class DeletePermissionHandler(
    Handler[DeletePermissionCommand, None, None], type_=HandlerType.WRITE
):
    db: Database

    async def __call__(self, cmd: DeletePermissionCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.permission.delete_by_id(cmd.id)
            await self.db.commit()
