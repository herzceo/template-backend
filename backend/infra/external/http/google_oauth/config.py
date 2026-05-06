from typing import Literal

from backend.internal.dto import StructDTO

type GoogleScope = Literal["openid", "email", "profile"]


class GoogleOAuthConfig(StructDTO):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    ACCOUNTS_BASE_URL: str = "https://accounts.google.com"
    OAUTH_BASE_URL: str = "https://oauth2.googleapis.com"
    API_BASE_URL: str = "https://www.googleapis.com"
    SCOPES: tuple[GoogleScope, ...] = ("openid", "email", "profile")
