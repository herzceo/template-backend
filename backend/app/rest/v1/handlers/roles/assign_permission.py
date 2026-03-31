from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class AssignPermissionCommand(Command):
    role_id: str
    permission_id: str


@dataclass
class AssignPermissionHandler(
    Handler[AssignPermissionCommand, None, None], type_=HandlerType.WRITE
):
    db: Database

    async def __call__(self, cmd: AssignPermissionCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.role.assign_permission(UUID(cmd.role_id), UUID(cmd.permission_id))
            await self.db.commit()
