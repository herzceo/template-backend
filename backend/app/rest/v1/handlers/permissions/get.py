from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class GetPermissionCommand(Command):
    id: UUID


@dataclass
class GetPermissionHandler(
    Handler[GetPermissionCommand, dtos.Permission, None], type_=HandlerType.READ
):
    db: Database

    async def __call__(self, cmd: GetPermissionCommand, _ctx: None = None) -> dtos.Permission:
        async with self.db:
            permission = (await self.db.gateway.permission.get_by_id(cmd.id)).some(NotFoundError())
        return dtos.Permission.from_object(permission)
