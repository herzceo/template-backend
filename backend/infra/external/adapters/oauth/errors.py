from dataclasses import dataclass

from backend.domain.enums import IdentityProvider
from backend.infra.external.errors import ExternalError


@dataclass
class OAuthAdapterError(ExternalError):
    message: str = "OAuth adapter error"


@dataclass
class UnsupportedProviderError(OAuthAdapterError):
    provider: IdentityProvider | None = None
    message: str = "Unsupported OAuth provider"
