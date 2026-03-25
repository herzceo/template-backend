from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class UpdateRoleCommand(Command):
    id: str
    name: str | None = None
    description: str | None = None


@dataclass
class UpdateRoleHandler(Handler[UpdateRoleCommand, dtos.Role, None], type_=HandlerType.WRITE):
    gateway: RepoGateway

    async def __call__(self, cmd: UpdateRoleCommand, _ctx: None = None) -> dtos.Role:
        entity = (await self.gateway.role.get_by_id(UUID(cmd.id))).some(NotFoundError())
        if cmd.name is not None:
            entity.name = cmd.name
        if cmd.description is not None:
            entity.description = cmd.description
        updated = (await self.gateway.role.update(entity)).some(NotFoundError())
        await self.gateway.commiter.commit()
        return dtos.Role.from_object(updated)
