from uuid import UUID

import msgspec.structs
from litestar import Controller, delete, get, patch, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import notifications
from backend.internal.di import Depends

from .dtos import DismissBody, MarkReadBody, ReactionBody, UpdateNotificationBody


class NotificationsController(Controller):
    path = ""
    tags = ("Notifications",)

    @get("/notifications/")
    async def list_notifications(
        self,
        handler: Depends[notifications.ListNotificationsHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.Notification]:
        return await handler(notifications.ListNotificationsCommand(offset=offset, limit=limit))

    @get("/notifications:listForUser")
    async def list_for_user(
        self,
        user_id: str,
        handler: Depends[notifications.ListUserNotificationsHandler],
        offset: int = 0,
        limit: int = 50,
        include_dismissed: bool = False,  # noqa: FBT001, FBT002
    ) -> dtos.PaginatedResponse[dtos.UserNotification]:
        return await handler(
            notifications.ListUserNotificationsCommand(
                user_id=UUID(user_id),
                offset=offset,
                limit=limit,
                include_dismissed=include_dismissed,
            )
        )

    @post("/notifications/")
    async def create_notification(
        self,
        data: notifications.CreateNotificationCommand,
        handler: Depends[notifications.CreateNotificationHandler],
    ) -> dtos.Notification:
        return await handler(data)

    @get("/notifications/{id:str}")
    async def get_notification(
        self,
        id: str,
        handler: Depends[notifications.GetNotificationHandler],
    ) -> dtos.Notification:
        return await handler(notifications.GetNotificationCommand(id=UUID(id)))

    @patch("/notifications/{id:str}")
    async def update_notification(
        self,
        id: str,
        data: UpdateNotificationBody,
        handler: Depends[notifications.UpdateNotificationHandler],
    ) -> dtos.Notification:
        return await handler(
            notifications.UpdateNotificationCommand(id=UUID(id), **msgspec.structs.asdict(data))
        )

    @delete("/notifications/{id:str}")
    async def delete_notification(
        self,
        id: str,
        handler: Depends[notifications.DeleteNotificationHandler],
    ) -> None:
        return await handler(notifications.DeleteNotificationCommand(id=UUID(id)))

    @post("/notifications/{id:str}:markRead")
    async def mark_read(
        self,
        id: str,
        data: MarkReadBody,
        handler: Depends[notifications.MarkReadHandler],
    ) -> None:
        return await handler(
            notifications.MarkReadCommand(notification_id=UUID(id), user_id=data.user_id)
        )

    @post("/notifications/{id:str}:dismiss")
    async def dismiss(
        self,
        id: str,
        data: DismissBody,
        handler: Depends[notifications.DismissHandler],
    ) -> None:
        return await handler(
            notifications.DismissCommand(notification_id=UUID(id), user_id=data.user_id)
        )

    @post("/notifications/{id:str}:react")
    async def react(
        self,
        id: str,
        data: ReactionBody,
        handler: Depends[notifications.ReactHandler],
    ) -> None:
        return await handler(
            notifications.ReactCommand(
                notification_id=UUID(id),
                user_id=data.user_id,
                reaction=data.reaction,
            )
        )
