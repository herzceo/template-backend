from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class AssignPermissionCommand(Command):
    role_id: UUID
    permission_id: UUID


@dataclass
class AssignPermissionHandler(
    Handler[AssignPermissionCommand, None, None], type_=HandlerType.WRITE
):
    db: Database

    async def __call__(self, cmd: AssignPermissionCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.role.assign_permission(cmd.role_id, cmd.permission_id)
            await self.db.commit()
