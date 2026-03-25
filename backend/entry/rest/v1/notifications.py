import msgspec.structs
from litestar import Controller, delete, get, patch, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import notifications
from backend.internal.di import Depends, inject

from .dtos import UpdateNotificationBody


class NotificationsController(Controller):
    path = "/notifications"
    tags = ("Notifications",)

    @get("/")
    @inject
    async def list_notifications(
        self,
        handler: Depends[notifications.ListNotificationsHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.Notification]:
        return await handler(notifications.ListNotificationsCommand(offset=offset, limit=limit))

    @post("/")
    @inject
    async def create_notification(
        self,
        data: notifications.CreateNotificationCommand,
        handler: Depends[notifications.CreateNotificationHandler],
    ) -> dtos.Notification:
        return await handler(data)

    @get("/{id:str}")
    @inject
    async def get_notification(
        self,
        id: str,
        handler: Depends[notifications.GetNotificationHandler],
    ) -> dtos.Notification:
        return await handler(notifications.GetNotificationCommand(id=id))

    @patch("/{id:str}")
    @inject
    async def update_notification(
        self,
        id: str,
        data: UpdateNotificationBody,
        handler: Depends[notifications.UpdateNotificationHandler],
    ) -> dtos.Notification:
        return await handler(
            notifications.UpdateNotificationCommand(id=id, **msgspec.structs.asdict(data))
        )

    @delete("/{id:str}")
    @inject
    async def delete_notification(
        self,
        id: str,
        handler: Depends[notifications.DeleteNotificationHandler],
    ) -> None:
        return await handler(notifications.DeleteNotificationCommand(id=id))

    @post("/{id:str}/read")
    @inject
    async def mark_read(
        self,
        id: str,
        user_id: str,
        handler: Depends[notifications.MarkReadHandler],
    ) -> None:
        return await handler(notifications.MarkReadCommand(notification_id=id, user_id=user_id))
