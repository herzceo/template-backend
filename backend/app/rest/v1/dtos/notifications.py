from datetime import datetime
from uuid import UUID

from backend.internal.dto import StructDTO


class Notification(StructDTO):
    id: UUID
    title: str
    body: str
    audience: str
    urgency: int
    target_id: UUID | None
    sender_id: UUID | None
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


class NotificationInteraction(StructDTO):
    notification_id: UUID
    user_id: UUID
    read_at: datetime | None
    dismissed_at: datetime | None
    reaction: str | None
    created_at: datetime
    updated_at: datetime


class UserNotification(StructDTO):
    notification: Notification
    interaction: NotificationInteraction | None
