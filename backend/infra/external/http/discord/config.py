from typing import Literal

from backend.internal.dto import StructDTO

type DiscordScope = Literal["identify", "email", "guilds", "bot", "connections"]


class DiscordOAuthConfig(StructDTO):
    DISCORD_CLIENT_ID: str
    DISCORD_CLIENT_SECRET: str
    DISCORD_REDIRECT_URI: str
    BASE_URL: str = "https://discord.com"
    SCOPES: tuple[DiscordScope, ...] = ("identify", "email")
