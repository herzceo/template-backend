from dataclasses import dataclass

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class ListUsersCommand(Command):
    offset: int = 0
    limit: int = 50


@dataclass
class ListUsersHandler(
    Handler[ListUsersCommand, dtos.PaginatedResponse[dtos.User], None],
    type_=HandlerType.READ,
):
    gateway: RepoGateway

    async def __call__(
        self, cmd: ListUsersCommand, _ctx: None = None
    ) -> dtos.PaginatedResponse[dtos.User]:
        items = await self.gateway.user.list_with_offset(offset=cmd.offset, limit=cmd.limit)
        total = await self.gateway.user.count()
        return dtos.PaginatedResponse(
            items=[dtos.User.from_object(i) for i in items],
            total=total,
            offset=cmd.offset,
            limit=cmd.limit,
        )
