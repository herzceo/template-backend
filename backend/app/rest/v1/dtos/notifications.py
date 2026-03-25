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
