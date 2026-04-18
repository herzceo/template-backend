from backend.domain.enums import IdentityProvider
from backend.internal.dto import StructDTO


class Redirect(StructDTO):
    url: str
    state: str


class IdentityDTO(StructDTO):
    id: str
    user_id: str
    provider: IdentityProvider
    provider_subject_id: str
    provider_email: str | None
    provider_display_name: str | None
    provider_avatar_url: str | None
    created_at: str
    updated_at: str


class InitiateResult(StructDTO):
    redirect: Redirect | None = None
    password_prompt: bool = False
