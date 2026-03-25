from dataclasses import dataclass

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class ListNotificationsCommand(Command):
    offset: int = 0
    limit: int = 50


@dataclass
class ListNotificationsHandler(
    Handler[ListNotificationsCommand, dtos.PaginatedResponse[dtos.Notification], None],
    type_=HandlerType.READ,
):
    gateway: RepoGateway

    async def __call__(
        self, cmd: ListNotificationsCommand, _ctx: None = None
    ) -> dtos.PaginatedResponse[dtos.Notification]:
        items = await self.gateway.notification.list_with_offset(offset=cmd.offset, limit=cmd.limit)
        total = await self.gateway.notification.count()
        return dtos.PaginatedResponse(
            items=[dtos.Notification.from_object(i) for i in items],
            total=total,
            offset=cmd.offset,
            limit=cmd.limit,
        )
