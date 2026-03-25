from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class GetRoleCommand(Command):
    id: str


@dataclass
class GetRoleHandler(Handler[GetRoleCommand, dtos.Role, None], type_=HandlerType.READ):
    gateway: RepoGateway

    async def __call__(self, cmd: GetRoleCommand, _ctx: None = None) -> dtos.Role:
        role = (await self.gateway.role.get_by_id(UUID(cmd.id))).some(NotFoundError())
        return dtos.Role.from_object(role)
