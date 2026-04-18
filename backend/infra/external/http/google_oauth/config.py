from typing import Literal

from backend.internal.dto import StructDTO

type GoogleScope = Literal["openid", "email", "profile"]


class GoogleOAuthSettings(StructDTO):
    CLIENT_ID: str
    CLIENT_SECRET: str
    REDIRECT_URI: str
    ACCOUNTS_BASE_URL: str = "https://accounts.google.com"
    OAUTH_BASE_URL: str = "https://oauth2.googleapis.com"
    API_BASE_URL: str = "https://www.googleapis.com"
    SCOPES: tuple[GoogleScope, ...] = ("openid", "email", "profile")
