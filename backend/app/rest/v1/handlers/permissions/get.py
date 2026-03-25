from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class GetPermissionCommand(Command):
    id: str


@dataclass
class GetPermissionHandler(
    Handler[GetPermissionCommand, dtos.Permission, None], type_=HandlerType.READ
):
    gateway: RepoGateway

    async def __call__(self, cmd: GetPermissionCommand, _ctx: None = None) -> dtos.Permission:
        permission = (await self.gateway.permission.get_by_id(UUID(cmd.id))).some(NotFoundError())
        return dtos.Permission.from_object(permission)
