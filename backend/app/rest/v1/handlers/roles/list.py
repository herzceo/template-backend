from dataclasses import dataclass

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class ListRolesCommand(Command):
    offset: int = 0
    limit: int = 50


@dataclass
class ListRolesHandler(
    Handler[ListRolesCommand, dtos.PaginatedResponse[dtos.Role], None],
    type_=HandlerType.READ,
):
    gateway: RepoGateway

    async def __call__(
        self, cmd: ListRolesCommand, _ctx: None = None
    ) -> dtos.PaginatedResponse[dtos.Role]:
        items = await self.gateway.role.list_with_offset(offset=cmd.offset, limit=cmd.limit)
        total = await self.gateway.role.count()
        return dtos.PaginatedResponse(
            items=[dtos.Role.from_object(i) for i in items],
            total=total,
            offset=cmd.offset,
            limit=cmd.limit,
        )
