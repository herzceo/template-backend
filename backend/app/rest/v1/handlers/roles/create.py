from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.entities.role import Role
from backend.domain.repos.gateway import RepoGateway


class CreateRoleCommand(Command):
    name: str
    tenant_id: str
    description: str | None = None


@dataclass
class CreateRoleHandler(Handler[CreateRoleCommand, dtos.Role, None], type_=HandlerType.WRITE):
    gateway: RepoGateway

    async def __call__(self, cmd: CreateRoleCommand, _ctx: None = None) -> dtos.Role:
        entity = Role(
            name=cmd.name,
            tenant_id=UUID(cmd.tenant_id),
            description=cmd.description,
        )
        created = (await self.gateway.role.create(entity)).some(AlreadyExistsError())
        await self.gateway.commiter.commit()
        return dtos.Role.from_object(created)
