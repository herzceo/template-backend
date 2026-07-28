from typing import ClassVar
from uuid import UUID

from backend.app.shared.events.base import BaseEvent


class EmailChangeRequested(BaseEvent):
    name: ClassVar[str] = "email_change_requested"
    user_id: UUID
    new_email: str
    username: str
    confirm_url: str
