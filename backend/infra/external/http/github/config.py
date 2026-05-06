from typing import Literal

from backend.internal.dto import StructDTO

type GitHubScope = Literal["read:user", "user:email", "repo", "gist"]


class GitHubOAuthConfig(StructDTO):
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str
    OAUTH_BASE_URL: str = "https://github.com"
    API_BASE_URL: str = "https://api.github.com"
    SCOPES: tuple[GitHubScope, ...] = ("read:user", "user:email")
