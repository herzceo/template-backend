from dataclasses import dataclass

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class ListSessionsCommand(Command):
    offset: int = 0
    limit: int = 50


@dataclass
class ListSessionsHandler(
    Handler[ListSessionsCommand, dtos.PaginatedResponse[dtos.Session], None],
    type_=HandlerType.READ,
):
    db: Database

    async def __call__(
        self, cmd: ListSessionsCommand, _ctx: None = None
    ) -> dtos.PaginatedResponse[dtos.Session]:
        async with self.db:
            items = await self.db.gateway.session_.list_with_offset(
                offset=cmd.offset, limit=cmd.limit
            )
            total = await self.db.gateway.session_.count()
            item_dtos = [dtos.Session.from_object(i) for i in items]
        return dtos.PaginatedResponse(
            items=item_dtos,
            total=total,
            offset=cmd.offset,
            limit=cmd.limit,
        )
