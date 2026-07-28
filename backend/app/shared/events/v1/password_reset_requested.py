from typing import ClassVar
from uuid import UUID

from backend.app.shared.events.base import BaseEvent


class PasswordResetRequested(BaseEvent):
    name: ClassVar[str] = "password_reset_requested"
    user_id: UUID
    email: str
    username: str
    reset_url: str
