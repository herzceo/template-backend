from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class DeleteRoleCommand(Command):
    id: UUID


@dataclass
class DeleteRoleHandler(Handler[DeleteRoleCommand, None, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: DeleteRoleCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.role.delete_by_id(cmd.id)
            await self.db.commit()
