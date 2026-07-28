from abc import abstractmethod
from typing import Protocol

from backend.internal import Option
from backend.internal.dto import StructDTO

# The window a provider-without-email signup has to supply an email, receive the
# code, and confirm it. Deliberately short: nothing exists server-side yet except
# this stash, and an abandoned one should evaporate.
OAUTH_SETUP_TTL_SECONDS = 15 * 60


class OAuthSetupSession(StructDTO, kw_only=True):
    """Server-side stash for an OAuth signup that arrived without an email.

    No ``User``/``Identity``/``UserEmail`` row exists yet — this is the *entire*
    record of the in-flight signup, held until the address is proven. Distinct
    from ``OneTimeTokenStore``, which is UUID-bound and cannot carry a payload.

    Provider access/refresh tokens are deliberately NOT stashed: nothing reads an
    OAuth identity's tokens here, and keeping them out of Redis keeps this record
    free of bearer credentials.
    """

    # Namespace key for the verification code store, which is UUID-keyed. There
    # is no user id yet, so the setup session mints its own.
    setup_id: str
    provider: str
    provider_subject_id: str
    provider_display_name: str | None = None
    provider_avatar_url: str | None = None
    # Soft anti-hijack binding to the device that started the setup (see
    # ``_common.check_setup_device``). Optional so ad-blocked clients still pass.
    device_fingerprint: str | None = None
    # Filled in by completeSignup once the user supplies them; still unproven
    # until confirmSignup verifies the emailed code.
    email: str | None = None
    canonical_email: str | None = None
    username: str | None = None


class OAuthSetupStore(Protocol):
    @abstractmethod
    async def issue(self, session: OAuthSetupSession, ttl_seconds: int) -> str:
        """Stash ``session`` and return the raw setup token. Only its hash is persisted."""
        ...

    @abstractmethod
    async def get(self, token: str) -> Option[OAuthSetupSession]:
        """Resolve ``token`` without consuming it. ``Option(None)`` when unknown or expired."""
        ...

    @abstractmethod
    async def update(self, token: str, session: OAuthSetupSession) -> bool:
        """Overwrite the stash for ``token``, preserving its remaining lifetime.

        Returns ``False`` when the token no longer exists, so a caller never
        resurrects an expired setup session by writing to it.
        """
        ...

    @abstractmethod
    async def consume(self, token: str) -> Option[OAuthSetupSession]:
        """Atomically resolve ``token`` and invalidate it. A replay resolves to None."""
        ...
