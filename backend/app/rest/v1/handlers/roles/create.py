from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.entities.role import Role
from backend.domain.repos.database import Database


class CreateRoleCommand(Command):
    name: str
    tenant_id: UUID
    description: str | None = None


@dataclass
class CreateRoleHandler(Handler[CreateRoleCommand, dtos.Role, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: CreateRoleCommand, _ctx: None = None) -> dtos.Role:
        async with self.db:
            entity = Role(
                name=cmd.name,
                tenant_id=cmd.tenant_id,
                description=cmd.description,
            )
            created = (await self.db.gateway.role.create(entity)).some(AlreadyExistsError())
            await self.db.commit()
        return dtos.Role.from_object(created)
