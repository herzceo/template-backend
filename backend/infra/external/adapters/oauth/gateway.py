from typing import final

from backend.app.ports.oauth_gateway import OAuthGateway, OAuthProviderAdapter
from backend.domain.enums import IdentityProvider

from .discord import ImplDiscordOAuthAdapter
from .github import ImplGitHubOAuthAdapter
from .google import ImplGoogleOAuthAdapter


@final
class ImplOAuthGateway(OAuthGateway):
    def __init__(
        self,
        google: ImplGoogleOAuthAdapter,
        github: ImplGitHubOAuthAdapter,
        discord: ImplDiscordOAuthAdapter,
    ) -> None:
        self._adapters: dict[IdentityProvider, OAuthProviderAdapter] = {
            IdentityProvider.GOOGLE: google,
            IdentityProvider.GITHUB: github,
            IdentityProvider.DISCORD: discord,
        }

    def get(self, provider: IdentityProvider) -> OAuthProviderAdapter:
        return self._adapters[provider]
