from typing import final
from urllib.parse import urlencode

from backend.app.shared.ports.auth.oauth_gateway import (
    AuthorizationURL,
    OAuthProviderAdapter,
    OAuthUserInfo,
)
from backend.domain.enums import IdentityProvider
from backend.infra.external.http.github import GitHubOAuthClient
from backend.infra.external.http.github.config import GitHubOAuthConfig
from backend.infra.external.http.github.endpoints import Endpoint


@final
class ImplGitHubOAuthAdapter(OAuthProviderAdapter):
    def __init__(self, client: GitHubOAuthClient, config: GitHubOAuthConfig) -> None:
        self._client = client
        self._config = config

    @property
    def provider(self) -> IdentityProvider:
        return IdentityProvider.GITHUB

    def get_authorization_url(self, state: str, redirect_uri: str) -> AuthorizationURL:
        params = {
            "client_id": self._config.GITHUB_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self._config.SCOPES),
            "state": state,
        }
        url = f"{self._config.OAUTH_BASE_URL}{Endpoint.OAUTH_AUTHORIZE}?{urlencode(params)}"
        return AuthorizationURL(url=url)

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthUserInfo:
        token = (await self._client.exchange_code(code, redirect_uri)).raise_()
        user = (await self._client.get_user_info(token.access_token)).raise_()

        email = user.email
        if email is None:
            emails = await self._client.get_emails(token.access_token)
            for entry in emails:
                if entry.primary and entry.verified:
                    email = entry.email
                    break

        return OAuthUserInfo(
            provider=IdentityProvider.GITHUB,
            subject_id=str(user.id),
            email=email,
            display_name=user.name or user.login,
            avatar_url=user.avatar_url,
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            scopes=token.scope,
        )
