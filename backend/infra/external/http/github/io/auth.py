from backend.infra.external.http.github.config import GitHubScope
from backend.internal.dto import StructDTO


class TokenResponse(StructDTO):
    access_token: str
    token_type: str
    scope: GitHubScope | None = None
    refresh_token: str | None = None


class UserInfoResponse(StructDTO):
    id: int
    login: str
    name: str | None = None
    email: str | None = None
    avatar_url: str | None = None


class EmailEntry(StructDTO):
    email: str
    primary: bool = False
    verified: bool = False
