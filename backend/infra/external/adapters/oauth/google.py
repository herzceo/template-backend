from typing import final
from urllib.parse import urlencode

from backend.app.shared.ports.auth.oauth_gateway import (
    AuthorizationURL,
    OAuthProviderAdapter,
    OAuthUserInfo,
)
from backend.domain.enums import IdentityProvider
from backend.infra.external.http.google_oauth import GoogleOAuthClient
from backend.infra.external.http.google_oauth.config import GoogleOAuthConfig
from backend.infra.external.http.google_oauth.endpoints import Endpoint


@final
class ImplGoogleOAuthAdapter(OAuthProviderAdapter):
    def __init__(self, client: GoogleOAuthClient, config: GoogleOAuthConfig) -> None:
        self._client = client
        self._config = config

    @property
    def provider(self) -> IdentityProvider:
        return IdentityProvider.GOOGLE

    def get_authorization_url(self, state: str) -> AuthorizationURL:
        params = {
            "client_id": self._config.CLIENT_ID,
            "redirect_uri": self._config.REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(self._config.SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        url = f"{self._config.ACCOUNTS_BASE_URL}{Endpoint.ACCOUNTS_AUTHORIZE}?{urlencode(params)}"
        return AuthorizationURL(url=url)

    async def exchange_code(self, code: str) -> OAuthUserInfo:
        token = (await self._client.exchange_code(code)).raise_()
        user = (await self._client.get_user_info(token.access_token)).raise_()
        return OAuthUserInfo(
            provider=IdentityProvider.GOOGLE,
            subject_id=user.sub,
            email=user.email,
            display_name=user.name,
            avatar_url=user.picture,
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            scopes=token.scope,
        )
