from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class UpdatePermissionCommand(Command):
    id: str
    codename: str | None = None
    description: str | None = None


@dataclass
class UpdatePermissionHandler(
    Handler[UpdatePermissionCommand, dtos.Permission, None], type_=HandlerType.WRITE
):
    gateway: RepoGateway

    async def __call__(self, cmd: UpdatePermissionCommand, _ctx: None = None) -> dtos.Permission:
        entity = (await self.gateway.permission.get_by_id(UUID(cmd.id))).some(NotFoundError())
        if cmd.codename is not None:
            entity.codename = cmd.codename
        if cmd.description is not None:
            entity.description = cmd.description
        updated = (await self.gateway.permission.update(entity)).some(NotFoundError())
        await self.gateway.commiter.commit()
        return dtos.Permission.from_object(updated)
