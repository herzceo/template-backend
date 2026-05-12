from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class UpdatePermissionCommand(Command):
    id: UUID
    codename: str | None = None
    description: str | None = None


@dataclass
class UpdatePermissionHandler(
    Handler[UpdatePermissionCommand, dtos.Permission, None], type_=HandlerType.WRITE
):
    db: Database

    async def __call__(self, cmd: UpdatePermissionCommand, _ctx: None = None) -> dtos.Permission:
        async with self.db:
            entity = (await self.db.gateway.permission.get_by_id(cmd.id)).some(NotFoundError())
            if cmd.codename is not None:
                entity.codename = cmd.codename
            if cmd.description is not None:
                entity.description = cmd.description
            updated = (await self.db.gateway.permission.update(entity)).some(NotFoundError())
            await self.db.commit()
        return dtos.Permission.from_object(updated)
