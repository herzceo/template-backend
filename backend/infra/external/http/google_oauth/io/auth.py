from backend.infra.external.http.google_oauth.config import GoogleScope
from backend.internal.dto import StructDTO


class TokenResponse(StructDTO):
    access_token: str
    token_type: str
    expires_in: int = 0
    refresh_token: str | None = None
    scope: GoogleScope | None = None


class UserInfoResponse(StructDTO):
    sub: str
    name: str | None = None
    email: str | None = None
    picture: str | None = None
    email_verified: bool = False
