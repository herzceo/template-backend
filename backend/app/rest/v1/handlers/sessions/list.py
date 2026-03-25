from dataclasses import dataclass

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class ListSessionsCommand(Command):
    offset: int = 0
    limit: int = 50


@dataclass
class ListSessionsHandler(
    Handler[ListSessionsCommand, dtos.PaginatedResponse[dtos.Session], None],
    type_=HandlerType.READ,
):
    gateway: RepoGateway

    async def __call__(
        self, cmd: ListSessionsCommand, _ctx: None = None
    ) -> dtos.PaginatedResponse[dtos.Session]:
        items = await self.gateway.session_.list_with_offset(offset=cmd.offset, limit=cmd.limit)
        total = await self.gateway.session_.count()
        return dtos.PaginatedResponse(
            items=[dtos.Session.from_object(i) for i in items],
            total=total,
            offset=cmd.offset,
            limit=cmd.limit,
        )
