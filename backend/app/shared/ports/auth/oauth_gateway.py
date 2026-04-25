from abc import abstractmethod
from typing import Protocol

from backend.domain.enums import IdentityProvider
from backend.internal.dto import StructDTO


class AuthorizationURL(StructDTO):
    url: str


class OAuthUserInfo(StructDTO):
    provider: IdentityProvider
    subject_id: str
    email: str | None
    display_name: str | None
    avatar_url: str | None
    access_token: str
    refresh_token: str | None
    scopes: str | None


class OAuthProviderAdapter(Protocol):
    @property
    @abstractmethod
    def provider(self) -> IdentityProvider: ...

    @abstractmethod
    def get_authorization_url(self, state: str) -> AuthorizationURL: ...

    @abstractmethod
    async def exchange_code(self, code: str) -> OAuthUserInfo: ...


class OAuthGateway(Protocol):
    @abstractmethod
    def get(self, provider: IdentityProvider) -> OAuthProviderAdapter: ...
