from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class AssignRoleCommand(Command):
    user_id: UUID
    role_id: UUID


@dataclass
class AssignRoleHandler(Handler[AssignRoleCommand, None, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: AssignRoleCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.user.assign_role(cmd.user_id, cmd.role_id)
            await self.db.commit()
