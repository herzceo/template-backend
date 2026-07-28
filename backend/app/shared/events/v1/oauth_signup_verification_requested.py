from typing import ClassVar
from uuid import UUID

from backend.app.shared.events.base import BaseEvent


class OAuthSignupVerificationRequested(BaseEvent):
    name: ClassVar[str] = "oauth_signup_verification_requested"
    setup_id: UUID
    email: str
    username: str
