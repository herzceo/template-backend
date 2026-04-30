from datetime import datetime
from uuid import UUID

from backend.domain.enums import IdentityProvider
from backend.internal.dto import StructDTO


class Redirect(StructDTO):
    url: str
    state: str


class IdentityDTO(StructDTO):
    id: UUID
    user_id: UUID
    provider: IdentityProvider
    provider_subject_id: str
    provider_email: str | None
    provider_display_name: str | None
    provider_avatar_url: str | None
    created_at: datetime
    updated_at: datetime


class InitiateResult(StructDTO):
    redirect: Redirect | None = None
    password_prompt: bool = False
