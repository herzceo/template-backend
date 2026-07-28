from typing import ClassVar
from uuid import UUID

from backend.app.shared.events.base import BaseEvent


class LoginCodeRequested(BaseEvent):
    name: ClassVar[str] = "login_code_requested"
    user_id: UUID
    email: str
    username: str
