from typing import ClassVar
from uuid import UUID

from backend.app.shared.events.base import BaseEvent


class OAuthIdentityAttached(BaseEvent):
    name: ClassVar[str] = "oauth_identity_attached"
    user_id: UUID
    email: str | None
    username: str
    provider: str
