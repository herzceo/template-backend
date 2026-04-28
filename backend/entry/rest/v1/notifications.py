from uuid import UUID

import msgspec.structs
from litestar import Controller, delete, get, patch, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import notifications
from backend.entry.rest.common.response import result
from backend.internal.di import Depends, inject

from .dtos import ReactionBody, UpdateNotificationBody


class NotificationsController(Controller):
    path = "/notifications"
    tags = ("Notifications",)

    @get("/")
    @inject
    @result
    async def list_notifications(
        self,
        handler: Depends[notifications.ListNotificationsHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.Notification]:
        return await handler(notifications.ListNotificationsCommand(offset=offset, limit=limit))

    @get("/for-user/{user_id:str}")
    @inject
    @result
    async def list_for_user(
        self,
        user_id: str,
        handler: Depends[notifications.ListUserNotificationsHandler],
        offset: int = 0,
        limit: int = 50,
        *,
        include_dismissed: bool = False,
    ) -> dtos.PaginatedResponse[dtos.UserNotification]:
        return await handler(
            notifications.ListUserNotificationsCommand(
                user_id=UUID(user_id),
                offset=offset,
                limit=limit,
                include_dismissed=include_dismissed,
            )
        )

    @post("/")
    @inject
    @result
    async def create_notification(
        self,
        data: notifications.CreateNotificationCommand,
        handler: Depends[notifications.CreateNotificationHandler],
    ) -> dtos.Notification:
        return await handler(data)

    @get("/{id:str}")
    @inject
    @result
    async def get_notification(
        self,
        id: str,
        handler: Depends[notifications.GetNotificationHandler],
    ) -> dtos.Notification:
        return await handler(notifications.GetNotificationCommand(id=UUID(id)))

    @patch("/{id:str}")
    @inject
    @result
    async def update_notification(
        self,
        id: str,
        data: UpdateNotificationBody,
        handler: Depends[notifications.UpdateNotificationHandler],
    ) -> dtos.Notification:
        return await handler(
            notifications.UpdateNotificationCommand(id=UUID(id), **msgspec.structs.asdict(data))
        )

    @delete("/{id:str}")
    @inject
    @result
    async def delete_notification(
        self,
        id: str,
        handler: Depends[notifications.DeleteNotificationHandler],
    ) -> None:
        return await handler(notifications.DeleteNotificationCommand(id=UUID(id)))

    @post("/{id:str}/read")
    @inject
    @result
    async def mark_read(
        self,
        id: str,
        user_id: str,
        handler: Depends[notifications.MarkReadHandler],
    ) -> None:
        return await handler(
            notifications.MarkReadCommand(notification_id=UUID(id), user_id=UUID(user_id))
        )

    @post("/{id:str}/dismiss")
    @inject
    @result
    async def dismiss(
        self,
        id: str,
        user_id: str,
        handler: Depends[notifications.DismissHandler],
    ) -> None:
        return await handler(
            notifications.DismissCommand(notification_id=UUID(id), user_id=UUID(user_id))
        )

    @post("/{id:str}/reaction")
    @inject
    @result
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
