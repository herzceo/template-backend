from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from backend.app.errors import (
    AlreadyExistsError,
    AuthenticationRequiredError,
    ValidationFailedError,
)
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.app_config import RateLimitConfig
from backend.app.rest.v1.handlers.auth._common import check_setup_device, enforce_rate_limit
from backend.app.rest.v1.handlers.auth.resend_verification import RESEND_COOLDOWN_SECONDS
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.validation import normalize_email, normalize_username
from backend.app.shared.db.database import Database
from backend.app.shared.events.v1.oauth_signup_verification_requested import (
    OAuthSignupVerificationRequested,
)
from backend.app.shared.ports.security.oauth_setup_store import OAuthSetupStore
from backend.app.shared.ports.security.rate_limiter import RateLimiter
from backend.app.shared.ports.security.verification import VerificationCodeStore


class CompleteOAuthSignupCommand(Command):
    # Read from the httpOnly setup cookie by the controller — never from the body.
    setup_token: str
    email: str
    username: str
    # Re-presented on every step so the setup session stays bound to its device.
    device_fingerprint: str | None = None
    ip: str | None = None


@dataclass
class CompleteOAuthSignupHandler(
    Handler[CompleteOAuthSignupCommand, dtos.OAuthSignupChallenge, None],
    type_=HandlerType.WRITE,
):
    """Take the email + username for an OAuth signup and mail a verification code.

    Creates no account. The response is byte-identical whether or not the address
    is already registered — this endpoint must not be an account oracle, so the
    ownership question is asked only at confirmSignup, after the address is
    proven. Re-calling it is the resend path, under the signup resend cooldown.
    """

    db: Database
    identity_service: IdentityService
    setup_store: OAuthSetupStore
    verification_store: VerificationCodeStore
    rate_limiter: RateLimiter
    rate_config: RateLimitConfig

    async def __call__(
        self, cmd: CompleteOAuthSignupCommand, _ctx: None = None
    ) -> dtos.OAuthSignupChallenge:
        await enforce_rate_limit(
            self.rate_limiter,
            cmd.ip and f"oauth_complete:{cmd.ip}",
            limit=self.rate_config.AUTH_RATE_LIMIT,
            window_seconds=self.rate_config.AUTH_RATE_WINDOW_SECONDS,
        )
        session = (await self.setup_store.get(cmd.setup_token)).some(
            AuthenticationRequiredError(
                message="This signup session expired, start again", code="setup_expired"
            )
        )
        check_setup_device(session, cmd.device_fingerprint)
        username = normalize_username(cmd.username)
        email = normalize_email(cmd.email)
        canonical = await self.identity_service.canonical_email(email)
        setup_id = UUID(session.setup_id)

        # Username availability is already public (usernameAvailable), so a real
        # 409 here leaks nothing new. Email ownership is NOT public and is
        # deliberately not consulted.
        async with self.db:
            if (await self.db.gateway.user.get_by_username(username)).value is not None:
                raise AlreadyExistsError(
                    message="This username is already taken", code="username_taken"
                )

        await self._enforce_cooldown(setup_id)

        session.email = email
        session.canonical_email = canonical
        session.username = username
        if not await self.setup_store.update(cmd.setup_token, session):
            raise AuthenticationRequiredError(
                message="This signup session expired, start again", code="setup_expired"
            )

        async with self.db:
            await self.db.dbus.publish(
                OAuthSignupVerificationRequested(setup_id=setup_id, email=email, username=username)
            )
            await self.db.commit()

        return dtos.OAuthSignupChallenge(
            ttl_seconds=self.verification_store.ttl_seconds,
            cooldown_seconds=RESEND_COOLDOWN_SECONDS,
        )

    async def _enforce_cooldown(self, setup_id: UUID) -> None:
        """Reject a re-send inside the cooldown, mirroring resendVerification."""
        entry = (await self.verification_store.get(setup_id)).value
        if entry is None or not entry.created_at:
            return
        try:
            issued_at = datetime.fromisoformat(entry.created_at)
        except ValueError:
            return
        elapsed = (datetime.now(UTC) - issued_at).total_seconds()
        if elapsed >= RESEND_COOLDOWN_SECONDS:
            return
        wait = int(RESEND_COOLDOWN_SECONDS - elapsed)
        raise ValidationFailedError(
            message=f"Please wait {wait} seconds before requesting a new code",
            details={"retry_after_seconds": str(wait)},
        )
