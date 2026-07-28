from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from backend.app.errors import (
    AlreadyExistsError,
    AuthenticationRequiredError,
    NotFoundError,
    ValidationFailedError,
)
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.dtos.auth import AuthContext
from backend.app.rest.v1.handlers.auth._common import (
    check_setup_device,
    consume_verification_code,
)
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.services.session import SessionService
from backend.app.rest.v1.services.types import ClientDeviceInfo
from backend.app.shared.db.database import Database
from backend.app.shared.events.v1.oauth_identity_attached import OAuthIdentityAttached
from backend.app.shared.ports.auth.oauth_gateway import OAuthUserInfo
from backend.app.shared.ports.security.oauth_setup_store import (
    OAuthSetupSession,
    OAuthSetupStore,
)
from backend.app.shared.ports.security.verification import VerificationCodeStore
from backend.domain.entities.profile import Profile
from backend.domain.entities.user import User
from backend.domain.enums import IdentityProvider


@dataclass(frozen=True)
class _Proven:
    """A setup session whose email has been proven — the fields are now non-None."""

    session: OAuthSetupSession
    email: str
    canonical_email: str
    username: str


@dataclass(frozen=True)
class _Materialized:
    user: User
    # True when the identity was attached to an ALREADY-EXISTING account rather
    # than creating one — the owner is told via OAuthIdentityAttached.
    attached_to_existing: bool


class ConfirmOAuthSignupCommand(Command):
    # Read from the httpOnly setup cookie by the controller — never from the body.
    setup_token: str
    code: str
    ip: str | None = None
    user_agent: str | None = None
    client_device: ClientDeviceInfo | None = None
    device_fingerprint: str | None = None


@dataclass
class ConfirmOAuthSignupHandler(
    Handler[ConfirmOAuthSignupCommand, AuthContext[dtos.User], None],
    type_=HandlerType.WRITE,
):
    """Prove the address, THEN decide whether to create an account or attach to one.

    The ordering is load-bearing. Branching on ownership before the code is
    verified would let an anonymous caller learn whether an address is registered
    and, worse, attach a provider identity to someone else's account. Only a
    proven address earns either outcome.
    """

    db: Database
    identity_service: IdentityService
    session_service: SessionService
    setup_store: OAuthSetupStore
    verification_store: VerificationCodeStore

    async def __call__(
        self, cmd: ConfirmOAuthSignupCommand, _ctx: None = None
    ) -> AuthContext[dtos.User]:
        session = (await self.setup_store.get(cmd.setup_token)).some(
            AuthenticationRequiredError(
                message="This signup session expired, start again", code="setup_expired"
            )
        )
        check_setup_device(session, cmd.device_fingerprint)
        if session.email is None or session.canonical_email is None or session.username is None:
            raise ValidationFailedError(message="No pending verification")

        setup_id = UUID(session.setup_id)
        await consume_verification_code(self.verification_store, setup_id, cmd.code)

        # From here the address is PROVEN. Only now may ownership decide anything.
        proven = _Proven(
            session=session,
            email=session.email,
            canonical_email=session.canonical_email,
            username=session.username,
        )
        provider = IdentityProvider(session.provider)
        async with self.db:
            materialized = await self._materialize(proven, provider)
            raw_token, _ = await self.session_service.create_session(
                materialized.user.id,
                ip=cmd.ip,
                user_agent=cmd.user_agent,
                client_device=cmd.client_device,
            )
            if materialized.attached_to_existing:
                await self.db.dbus.publish(
                    OAuthIdentityAttached(
                        user_id=materialized.user.id,
                        email=proven.email,
                        username=materialized.user.username,
                        provider=provider.value,
                    )
                )
            await self.db.commit()

        await self.setup_store.consume(cmd.setup_token)

        return AuthContext(
            token=raw_token,
            data=dtos.User.from_object(materialized.user),
        )

    async def _materialize(self, proven: _Proven, provider: IdentityProvider) -> _Materialized:
        # A concurrent (or replayed) confirm may already have linked this identity.
        # Resolving it first makes a double-submit idempotent instead of a
        # unique-violation 500.
        already = (
            await self.db.gateway.identity.get_by_provider_subject(
                provider, proven.session.provider_subject_id
            )
        ).value
        if already is not None:
            return _Materialized(
                user=await self._load_user(already.user_id), attached_to_existing=False
            )

        owner_id = await self.identity_service.email_owner_id(proven.canonical_email)
        if owner_id is not None:
            return await self._attach_to_owner(proven, provider, owner_id)
        return await self._create_account(proven, provider)

    async def _attach_to_owner(
        self, proven: _Proven, provider: IdentityProvider, owner_id: UUID
    ) -> _Materialized:
        """The address is already an account's — attach the identity, never create."""
        user = (await self.db.gateway.user.get_for_update(owner_id)).some(
            AuthenticationRequiredError(message="User not found")
        )
        raced = (
            await self.db.gateway.identity.get_by_provider_subject(
                provider, proven.session.provider_subject_id
            )
        ).value
        if raced is not None:
            return _Materialized(
                user=await self._load_user(raced.user_id), attached_to_existing=False
            )

        await self.identity_service.link_oauth_identity(
            user.id, self._provider_info(proven.session, provider)
        )
        (
            await self.identity_service.register_email(
                user.id,
                proven.email,
                proven.canonical_email,
                provider=provider,
                verified=True,
            )
        ).some(AlreadyExistsError(message="This email is already registered", code="email_taken"))
        await self.identity_service.verify_user_on_matching_email(user, proven.email)
        return _Materialized(user=user, attached_to_existing=True)

    async def _create_account(self, proven: _Proven, provider: IdentityProvider) -> _Materialized:
        """Nobody owns the address — this is where the account finally comes into being."""
        default_tenant = (await self.db.gateway.tenant.get_default()).some(
            NotFoundError(message="No default tenant configured")
        )
        created = (
            await self.db.gateway.user.create(
                User(
                    username=proven.username,
                    email=proven.email,
                    tenant_id=default_tenant.id,
                    # The address was just proven, so the account is born verified.
                    verified_at=datetime.now(UTC),
                    # The user typed this username themselves — no onboarding step.
                    username_confirmed=True,
                )
            )
        ).value
        if created is None:
            # A username or email was claimed between the ownership read and here.
            # An email race is already proven, so re-resolve and attach; a username
            # race is the caller's to remedy (start over at completeSignup).
            owner_id = await self.identity_service.email_owner_id(proven.canonical_email)
            if owner_id is not None:
                return await self._attach_to_owner(proven, provider, owner_id)
            raise AlreadyExistsError(
                message="This username is already taken", code="username_taken"
            )

        (
            await self.db.gateway.profile.create(
                Profile(
                    user_id=created.id,
                    display_name=proven.session.provider_display_name,
                    avatar_url=proven.session.provider_avatar_url,
                )
            )
        ).some(RuntimeError("Failed to create profile"))
        await self.identity_service.link_oauth_identity(
            created.id, self._provider_info(proven.session, provider)
        )
        (
            await self.identity_service.register_email(
                created.id,
                proven.email,
                proven.canonical_email,
                is_primary=True,
                provider=provider,
                verified=True,
            )
        ).some(AlreadyExistsError(message="This email is already registered", code="email_taken"))
        return _Materialized(user=created, attached_to_existing=False)

    async def _load_user(self, user_id: UUID) -> User:
        return (await self.db.gateway.user.get_by_id(user_id)).some(
            AuthenticationRequiredError(message="User not found")
        )

    @staticmethod
    def _provider_info(session: OAuthSetupSession, provider: IdentityProvider) -> OAuthUserInfo:
        """Rebuild the provider profile from the stash.

        ``email`` stays None on purpose: the provider never reported one, so
        ``identity.provider_email`` must not claim the address the user typed.
        Access/refresh tokens were never stashed, so they are empty here and the
        identity's token columns stay NULL.
        """
        return OAuthUserInfo(
            provider=provider,
            subject_id=session.provider_subject_id,
            email=None,
            display_name=session.provider_display_name,
            avatar_url=session.provider_avatar_url,
            access_token="",
            refresh_token=None,
            scopes=None,
        )
