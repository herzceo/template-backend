from typing import Literal

from backend.internal.dto import StructDTO

type DiscordScope = Literal["identify", "email", "guilds", "bot", "connections"]


class DiscordOAuthConfig(StructDTO):
    CLIENT_ID: str
    CLIENT_SECRET: str
    REDIRECT_URI: str
    BASE_URL: str = "https://discord.com"
    SCOPES: tuple[DiscordScope, ...] = ("identify", "email")
