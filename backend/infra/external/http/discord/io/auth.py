from backend.infra.external.http.discord.config import DiscordScope
from backend.internal.dto import StructDTO


class TokenResponse(StructDTO):
    access_token: str
    token_type: str
    expires_in: int = 0
    refresh_token: str | None = None
    scope: DiscordScope | None = None


class UserInfoResponse(StructDTO):
    id: str
    username: str
    global_name: str | None = None
    avatar: str | None = None
    email: str | None = None
