from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class GetRoleCommand(Command):
    id: UUID


@dataclass
class GetRoleHandler(Handler[GetRoleCommand, dtos.Role, None], type_=HandlerType.READ):
    db: Database

    async def __call__(self, cmd: GetRoleCommand, _ctx: None = None) -> dtos.Role:
        async with self.db:
            role = (await self.db.gateway.role.get_by_id(cmd.id)).some(NotFoundError())
        return dtos.Role.from_object(role)
