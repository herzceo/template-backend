from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class UpdateRoleCommand(Command):
    id: UUID
    name: str | None = None
    description: str | None = None


@dataclass
class UpdateRoleHandler(Handler[UpdateRoleCommand, dtos.Role, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: UpdateRoleCommand, _ctx: None = None) -> dtos.Role:
        async with self.db:
            entity = (await self.db.gateway.role.get_by_id(cmd.id)).some(NotFoundError())
            if cmd.name is not None:
                entity.name = cmd.name
            if cmd.description is not None:
                entity.description = cmd.description
            updated = (await self.db.gateway.role.update(entity)).some(NotFoundError())
            await self.db.commit()
        return dtos.Role.from_object(updated)
