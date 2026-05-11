from dataclasses import dataclass

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class ListPermissionsCommand(Command):
    offset: int = 0
    limit: int = 50


@dataclass
class ListPermissionsHandler(
    Handler[ListPermissionsCommand, dtos.PaginatedResponse[dtos.Permission], None],
    type_=HandlerType.READ,
):
    db: Database

    async def __call__(
        self, cmd: ListPermissionsCommand, _ctx: None = None
    ) -> dtos.PaginatedResponse[dtos.Permission]:
        async with self.db:
            items = await self.db.gateway.permission.list_with_offset(
                offset=cmd.offset, limit=cmd.limit
            )
            total = await self.db.gateway.permission.count()
        return dtos.PaginatedResponse(
            items=[dtos.Permission.from_object(i) for i in items],
            total=total,
            offset=cmd.offset,
            limit=cmd.limit,
        )
