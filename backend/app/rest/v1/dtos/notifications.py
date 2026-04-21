from backend.internal.dto import StructDTO


class Notification(StructDTO):
    id: str
    title: str
    body: str
    audience: str
    urgency: int
    target_id: str | None
    sender_id: str | None
    tenant_id: str
    created_at: str
    updated_at: str


class NotificationInteraction(StructDTO):
    notification_id: str
    user_id: str
    read_at: str | None
    dismissed_at: str | None
    reaction: str | None
    created_at: str
    updated_at: str


class UserNotification(StructDTO):
    notification: Notification
    interaction: NotificationInteraction | None
