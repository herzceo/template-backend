from dataclasses import dataclass

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database
from backend.domain.entities.permission import Permission


class CreatePermissionCommand(Command):
    codename: str
    description: str | None = None


@dataclass
class CreatePermissionHandler(
    Handler[CreatePermissionCommand, dtos.Permission, None], type_=HandlerType.WRITE
):
    db: Database

    async def __call__(self, cmd: CreatePermissionCommand, _ctx: None = None) -> dtos.Permission:
        async with self.db:
            entity = Permission(
                codename=cmd.codename,
                description=cmd.description,
            )
            created = (await self.db.gateway.permission.create(entity)).some(AlreadyExistsError())
            await self.db.commit()
        return dtos.Permission.from_object(created)
