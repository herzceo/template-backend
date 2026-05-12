from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class ListNotificationsCommand(Command):
    offset: int = 0
    limit: int = 50


@dataclass
class ListNotificationsHandler(
    Handler[ListNotificationsCommand, dtos.PaginatedResponse[dtos.Notification], None],
    type_=HandlerType.READ,
):
    db: Database

    async def __call__(
        self, cmd: ListNotificationsCommand, _ctx: None = None
    ) -> dtos.PaginatedResponse[dtos.Notification]:
        async with self.db:
            items = await self.db.gateway.notification.list_with_offset(
                offset=cmd.offset, limit=cmd.limit
            )
            total = await self.db.gateway.notification.count()
        return dtos.PaginatedResponse(
            items=[dtos.Notification.from_object(i) for i in items],
            total=total,
            offset=cmd.offset,
            limit=cmd.limit,
        )


class ListUserNotificationsCommand(Command):
    user_id: UUID
    offset: int = 0
    limit: int = 50
    include_dismissed: bool = False


@dataclass
class ListUserNotificationsHandler(
    Handler[
        ListUserNotificationsCommand,
        dtos.PaginatedResponse[dtos.UserNotification],
        None,
    ],
    type_=HandlerType.READ,
):
    db: Database

    async def __call__(
        self, cmd: ListUserNotificationsCommand, _ctx: None = None
    ) -> dtos.PaginatedResponse[dtos.UserNotification]:
        async with self.db:
            rows = await self.db.gateway.notification.list_for_user(
                cmd.user_id,
                offset=cmd.offset,
                limit=cmd.limit,
                include_dismissed=cmd.include_dismissed,
            )
            total = await self.db.gateway.notification.count_for_user(
                cmd.user_id, include_dismissed=cmd.include_dismissed
            )
        return dtos.PaginatedResponse(
            items=[
                dtos.UserNotification(
                    notification=dtos.Notification.from_object(n),
                    interaction=(
                        dtos.NotificationInteraction.from_object(i) if i is not None else None
                    ),
                )
                for n, i in rows
            ],
            total=total,
            offset=cmd.offset,
            limit=cmd.limit,
        )
