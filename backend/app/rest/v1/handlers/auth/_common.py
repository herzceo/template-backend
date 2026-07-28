from datetime import UTC, datetime
from uuid import UUID

from backend.app.errors import (
    AuthenticationRequiredError,
    InvalidInputError,
    ValidationFailedError,
)
from backend.app.rest.v1.validation import normalize_email, normalize_username
from backend.app.shared.db.database import Database
from backend.app.shared.ports.security.oauth_setup_store import OAuthSetupSession
from backend.app.shared.ports.security.rate_limiter import RateLimiter
from backend.app.shared.ports.security.verification import (
    VerificationCodeStore,
    VerificationEntry,
)
from backend.domain.entities.user import User
from backend.internal import Option


async def enforce_rate_limit(
    rate_limiter: RateLimiter, key: str | None, *, limit: int, window_seconds: int
) -> None:
    """Throttle a public request endpoint per fixed window, or raise.

    ``key`` is the caller's IP (server-derived). The decision is taken BEFORE any
    user lookup so it never depends on whether an account exists — keeping the
    request endpoints enumeration-safe. A ``None`` key (no client IP) is not
    throttled.
    """
    if not key:
        return
    decision = await rate_limiter.hit(key, limit=limit, window_seconds=window_seconds)
    if not decision.allowed:
        raise ValidationFailedError(
            message="Too many requests, please slow down",
            code="rate_limited",
            details={"retry_after_seconds": str(decision.retry_after)},
        )


async def resolve_user_by_identifier(db: Database, identifier: str) -> Option[User]:
    """Resolve a user from an email-or-username identifier.

    "@" in the identifier selects the email lookup, otherwise username. A
    malformed identifier resolves to ``Option(None)`` rather than raising, so the
    neutral request endpoints (login-code / password-reset request) never reveal
    whether an account exists. Opens and closes its own transaction.
    """
    try:
        if "@" in identifier:
            email = normalize_email(identifier)
            async with db:
                return await db.gateway.user.get_by_email(email)
        username = normalize_username(identifier)
        async with db:
            return await db.gateway.user.get_by_username(username)
    except InvalidInputError:
        return Option(None)


def check_setup_device(session: OAuthSetupSession, presented: str | None) -> None:
    """Bind an OAuth setup session to the device that began it — softly.

    The setup token rides in an httpOnly cookie, but ``exchange_oauth_code``
    resolves identity by ``(provider, subject_id)`` alone: whoever holds the token
    can finish the signup against an address they control, after which the
    victim's "Sign in with {Provider}" permanently lands in the attacker's
    account. Requiring the fingerprint the flow started with narrows a leaked
    cookie to a leaked cookie *plus* the originating browser.

    Deliberately soft. A device fingerprint fetched from a CDN that ad blockers
    and corporate proxies can block means ``None`` on either side is a normal
    outcome for a real user — and a legitimate fingerprint can change mid-flow.
    Only two values that are both present and different are a rejection; anything
    else must let the signup through rather than strand someone at the last step.
    """
    captured = session.device_fingerprint
    if captured and presented and captured != presented:
        raise AuthenticationRequiredError(
            message="This signup was started on a different device, start again",
            code="setup_device_mismatch",
        )


def too_many_attempts_error(
    store: VerificationCodeStore, entry: VerificationEntry
) -> ValidationFailedError:
    """Attempts reset when the code expires -- surface that as retry_after."""
    details: dict[str, str] = {}
    if entry.created_at:
        try:
            issued_at = datetime.fromisoformat(entry.created_at)
        except ValueError:
            issued_at = None
        if issued_at is not None:
            elapsed = (datetime.now(UTC) - issued_at).total_seconds()
            remaining = max(0, int(store.ttl_seconds - elapsed))
            details["retry_after_seconds"] = str(remaining)
    return ValidationFailedError(message="Too many attempts, request a new code", details=details)


async def consume_verification_code(store: VerificationCodeStore, key: UUID, code: str) -> None:
    """Check ``code`` against the pending entry for ``key``, or raise.

    Returns cleanly only when the code matched (the store then drops the entry).
    ``key`` is the user id for the email/password flow and the setup-session id
    for the OAuth signup flow — the store only ever treats it as a namespace.
    """
    entry = (await store.get(key)).some(ValidationFailedError(message="No pending verification"))
    if entry.attempts >= store.max_attempts:
        raise too_many_attempts_error(store, entry)
    if await store.verify(key, code):
        return
    updated = (await store.get(key)).value
    remaining = store.max_attempts - (updated.attempts if updated else 0)
    if remaining <= 0:
        raise too_many_attempts_error(store, updated or entry)
    raise ValidationFailedError(message=f"Invalid code, {remaining} attempt(s) remaining")
