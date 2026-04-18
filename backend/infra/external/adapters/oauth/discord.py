from typing import final
from urllib.parse import urlencode

from backend.app.ports.oauth_gateway import (
    AuthorizationURL,
    OAuthProviderAdapter,
    OAuthUserInfo,
)
from backend.domain.enums import IdentityProvider
from backend.infra.external.http.discord import DiscordOAuthClient
from backend.infra.external.http.discord.config import DiscordOAuthSettings
from backend.infra.external.http.discord.endpoints import Endpoint


@final
class ImplDiscordOAuthAdapter(OAuthProviderAdapter):
    def __init__(self, client: DiscordOAuthClient, settings: DiscordOAuthSettings) -> None:
        self._client = client
        self._settings = settings

    @property
    def provider(self) -> IdentityProvider:
        return IdentityProvider.DISCORD

    def get_authorization_url(self, state: str) -> AuthorizationURL:
        params = {
            "client_id": self._settings.CLIENT_ID,
            "redirect_uri": self._settings.REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(self._settings.SCOPES),
            "state": state,
        }
        url = f"{self._settings.BASE_URL}{Endpoint.OAUTH_AUTHORIZE}?{urlencode(params)}"
        return AuthorizationURL(url=url)

    async def exchange_code(self, code: str) -> OAuthUserInfo:
        token = (await self._client.exchange_code(code)).raise_()
        user = (await self._client.get_user_info(token.access_token)).raise_()

        avatar_url = None
        if user.avatar:
            avatar_url = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.png"

        return OAuthUserInfo(
            provider=IdentityProvider.DISCORD,
            subject_id=user.id,
            email=user.email,
            display_name=user.global_name or user.username,
            avatar_url=avatar_url,
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            scopes=token.scope,
        )
