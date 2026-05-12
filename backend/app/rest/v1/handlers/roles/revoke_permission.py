from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class RevokePermissionCommand(Command):
    role_id: UUID
    permission_id: UUID


@dataclass
class RevokePermissionHandler(
    Handler[RevokePermissionCommand, None, None], type_=HandlerType.WRITE
):
    db: Database

    async def __call__(self, cmd: RevokePermissionCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.role.revoke_permission(cmd.role_id, cmd.permission_id)
            await self.db.commit()
