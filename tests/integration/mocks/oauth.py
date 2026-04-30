from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, final

from backend.app.shared.ports.auth.oauth_gateway import (
    AuthorizationURL,
    OAuthProviderAdapter,
    OAuthUserInfo,
)

if TYPE_CHECKING:
    from backend.domain.enums import IdentityProvider


class _MockOAuthAdapter:
    def __init__(self, provider: IdentityProvider, info: OAuthUserInfo | None) -> None:
        self._provider = provider
        self._info = info

    @property
    def provider(self) -> IdentityProvider:
        return self._provider

    def get_authorization_url(self, state: str) -> AuthorizationURL:
        return AuthorizationURL(url=f"https://mock-oauth/{self._provider.value}?state={state}")

    async def exchange_code(self, _code: str) -> OAuthUserInfo:
        if self._info is None:
            msg = (
                f"MockOAuthGateway not configured for {self._provider}: call set_user_info() first"
            )
            raise RuntimeError(msg)
        return self._info


@final
@dataclass
class MockOAuthGateway:
    _profiles: dict[IdentityProvider, OAuthUserInfo] = field(default_factory=dict)

    def set_user_info(self, provider: IdentityProvider, info: OAuthUserInfo) -> None:
        self._profiles[provider] = info

    def get(self, provider: IdentityProvider) -> OAuthProviderAdapter:
        return _MockOAuthAdapter(provider=provider, info=self._profiles.get(provider))
