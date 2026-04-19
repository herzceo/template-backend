from typing import ClassVar
from uuid import UUID

from backend.app.shared.events.base import BaseEvent


class UserVerificationRequested(BaseEvent):
    name: ClassVar[str] = "user_verification_requested"
    user_id: UUID
    email: str
    username: str
