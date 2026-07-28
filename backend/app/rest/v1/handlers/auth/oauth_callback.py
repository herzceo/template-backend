import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.app.errors import AlreadyExistsError, AuthenticationRequiredError, NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.services.session import SessionService
from backend.app.rest.v1.validation import normalize_email
from backend.app.shared.db.database import Database
from backend.app.shared.ports.auth.oauth_gateway import OAuthUserInfo
from backend.app.shared.ports.security.oauth_setup_store import (
    OAUTH_SETUP_TTL_SECONDS,
    OAuthSetupSession,
    OAuthSetupStore,
)
from backend.domain.entities.profile import Profile
from backend.domain.entities.user import User
from backend.domain.enums import IdentityProvider

# Everything outside [a-z0-9] is stripped from the provider display name to seed a
# clean username handle (e.g. "Jane CEO" -> "janeceo").
_USERNAME_SLUG_RE = re.compile(r"[^a-z0-9]")
_USERNAME_MIN = 3
_USERNAME_BASE_MAX = 24
_USERNAME_MAX = 32


@dataclass(frozen=True)
class _AccountSession:
    """An OAuth callback that resolved to a real account and a live session."""

    user: User
    session_token: str


class OAuthCallbackCommand(Command):
    provider: IdentityProvider
    code: str
    state: str
    # Must byte-match the redirect_uri sent at initiate (OAuth token exchange
    # requires it). The controller recomputes it from the callback request host.
    redirect_uri: str
    # Client-supplied device fingerprint, carried into the setup stash so a
    # no-email signup stays bound to the device that began it.
    device_fingerprint: str | None = None


@dataclass
class OAuthCallbackHandler(
    Handler[OAuthCallbackCommand, dtos.OAuthCallbackOutcome, None],
    type_=HandlerType.WRITE,
):
    db: Database
    identity_service: IdentityService
    session_service: SessionService
    setup_store: OAuthSetupStore

    async def __call__(
        self, cmd: OAuthCallbackCommand, _ctx: None = None
    ) -> dtos.OAuthCallbackOutcome:
        resolved: _AccountSession | None = None

        async with self.db:
            identity, user_info = await self.identity_service.exchange_oauth_code(
                cmd.provider, cmd.code, cmd.state, cmd.redirect_uri
            )

            # The verified provider email lets us canonicalize and try to attach
            # this identity to an existing account (auto-link) before creating one.
            email = normalize_email(user_info.email) if user_info.email else None

            if identity is not None:
                user = (await self.db.gateway.user.get_by_id(identity.user_id)).some(
                    AuthenticationRequiredError(message="User not found")
                )
                await self.identity_service.verify_user_on_matching_email(user, email)
                resolved = _AccountSession(user=user, session_token=await self._start_session(user))
            elif email is not None:
                resolved = await self._signup_or_link(cmd, user_info, email)
            if resolved is not None:
                await self.db.commit()

        # A brand-new identity whose provider reported no email creates NOTHING
        # here — no User, no Identity, no UserEmail. The account comes into
        # existence only once the address is proven, at confirmSignup (B3).
        if resolved is None:
            setup_token = await self._begin_setup(cmd, user_info)
            return dtos.OAuthCallbackOutcome(
                result=dtos.OAuthCallbackResult(setup_required=True),
                setup_token=setup_token,
            )

        return dtos.OAuthCallbackOutcome(
            result=dtos.OAuthCallbackResult(
                setup_required=False,
                user=dtos.User.from_object(resolved.user),
            ),
            session_token=resolved.session_token,
        )

    async def _begin_setup(self, cmd: OAuthCallbackCommand, user_info: OAuthUserInfo) -> str:
        """Stash the provider result and mint the setup token (cookie-only)."""
        session = OAuthSetupSession(
            setup_id=str(uuid4()),
            provider=cmd.provider.value,
            provider_subject_id=user_info.subject_id,
            provider_display_name=user_info.display_name,
            provider_avatar_url=user_info.avatar_url,
            device_fingerprint=cmd.device_fingerprint,
        )
        return await self.setup_store.issue(session, OAUTH_SETUP_TTL_SECONDS)

    async def _signup_or_link(
        self, cmd: OAuthCallbackCommand, user_info: OAuthUserInfo, email: str
    ) -> _AccountSession:
        """An unknown identity that DOES carry an email: auto-link it or create."""
        canonical = await self.identity_service.canonical_email(email)

        owner_id = await self.identity_service.email_owner_id(canonical)
        if owner_id is None:
            created = await self._create_account(cmd, user_info, email, canonical)
            if created is not None:
                return _AccountSession(
                    user=created, session_token=await self._start_session(created)
                )
            # A concurrent signup claimed the address between the ownership read and
            # the INSERT. The provider already verified it, so the outcome is the
            # one a non-racing caller would have got: link, don't create.
            owner_id = await self.identity_service.email_owner_id(canonical)
            if owner_id is None:
                raise AlreadyExistsError(
                    message="This email is already registered", code="email_taken"
                )

        user = await self._link_to_existing(cmd.provider, owner_id, user_info, canonical)
        return _AccountSession(user=user, session_token=await self._start_session(user))

    async def _start_session(self, user: User) -> str:
        raw_token, _ = await self.session_service.create_session(user.id)
        return raw_token

    async def _link_to_existing(
        self,
        provider: IdentityProvider,
        owner_id: UUID,
        user_info: OAuthUserInfo,
        canonical: str,
    ) -> User:
        """Attach a new OAuth identity to the account that already owns its email."""
        user = (await self.db.gateway.user.get_by_id(owner_id)).some(
            AuthenticationRequiredError(message="User not found")
        )
        await self.identity_service.link_oauth_identity(user.id, user_info)
        provider_email = normalize_email(user_info.email) if user_info.email else None
        await self.identity_service.register_email(
            user.id,
            provider_email or canonical,
            canonical,
            provider=provider,
            verified=True,
        )
        await self.identity_service.verify_user_on_matching_email(user, provider_email)
        return user

    async def _create_account(
        self,
        cmd: OAuthCallbackCommand,
        user_info: OAuthUserInfo,
        email: str,
        canonical: str,
    ) -> User | None:
        """Create the account, or ``None`` when the address was claimed mid-flight."""
        default_tenant = (await self.db.gateway.tenant.get_default()).some(
            NotFoundError(message="No default tenant configured")
        )
        username = await self._generate_preset_username(user_info.display_name, cmd.provider)
        user_entity = User(
            username=username,
            email=email,
            tenant_id=default_tenant.id,
            # The provider asserted this address, so the account is born verified.
            verified_at=datetime.now(UTC),
            # Auto-generated preset — the user confirms/edits it once at onboarding.
            username_confirmed=False,
        )
        created = (await self.db.gateway.user.create(user_entity)).value
        if created is None:
            # Either the email or the username was claimed concurrently. The caller
            # re-reads ownership: an email race becomes an auto-link, anything else
            # surfaces as a conflict.
            return None
        profile = Profile(
            user_id=created.id,
            display_name=user_info.display_name,
            avatar_url=user_info.avatar_url,
        )
        (await self.db.gateway.profile.create(profile)).some(
            RuntimeError("Failed to create profile")
        )
        await self.identity_service.link_oauth_identity(created.id, user_info)
        (
            await self.identity_service.register_email(
                created.id, email, canonical, is_primary=True, provider=cmd.provider, verified=True
            )
        ).some(AlreadyExistsError(message="This email is already registered", code="email_taken"))
        return created

    async def _generate_preset_username(
        self, display_name: str | None, provider: IdentityProvider
    ) -> str:
        """Seed a clean, available username from the provider's display name.

        Slugified handle first (``janeceo``); on collision, a short random numeric
        suffix. Only a starting point — the account is marked unconfirmed so the
        user chooses/confirms it at onboarding.
        """
        base = _USERNAME_SLUG_RE.sub("", (display_name or "").lower())[:_USERNAME_BASE_MAX]
        if len(base) < _USERNAME_MIN:
            base = f"{provider.value}user"[:_USERNAME_BASE_MAX]
        candidate = base
        for _ in range(6):
            if (await self.db.gateway.user.get_by_username(candidate)).value is None:
                return candidate
            candidate = f"{base}{secrets.randbelow(9000) + 1000}"
        return f"{base}{secrets.token_hex(4)}"[:_USERNAME_MAX]
