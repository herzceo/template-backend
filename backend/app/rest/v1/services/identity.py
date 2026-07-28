from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from backend.app.errors import (
    AlreadyExistsError,
    AuthenticationRequiredError,
    ValidationFailedError,
)
from backend.app.rest.v1.dtos.identity import InitiateResult, Redirect
from backend.app.rest.v1.validation import normalize_email, normalize_username
from backend.app.shared.db.database import Database
from backend.app.shared.ports.auth.email_normalizer import EmailNormalizer
from backend.app.shared.ports.auth.oauth_gateway import OAuthGateway, OAuthUserInfo
from backend.app.shared.ports.auth.oauth_state import OAuthStateSigner
from backend.app.shared.ports.auth.password_hasher import PasswordHasher
from backend.domain.entities.identity import Identity
from backend.domain.entities.user import User
from backend.domain.entities.user_email import UserEmail
from backend.domain.enums import IdentityProvider
from backend.internal import Option

# Email-change confirmation link lifetime — long enough to reach an inbox and act.
_EMAIL_CHANGE_TTL_SECONDS = 30 * 60

# Field counts for the pipe-delimited signed-token payloads.
_EMAIL_CHANGE_PARTS = 4
_REAUTH_PARTS = 2
_LINK_PARTS = 2
# State prefixes that are step-up flows bound to a logged-in user — they must
# never be accepted by the public login/signup callback (would switch accounts).
_STEP_UP_PREFIXES = ("reauth", "link")


@dataclass
class IdentityService:
    db: Database
    password_hasher: PasswordHasher
    oauth_gateway: OAuthGateway
    state_signer: OAuthStateSigner
    email_normalizer: EmailNormalizer

    async def canonical_email(self, email: str) -> str:
        """Aggressive, provider-aware canonical form — the global-uniqueness key."""
        return await self.email_normalizer.canonical(email)

    async def verify_user_on_matching_email(self, user: User, provider_email: str | None) -> bool:
        """Verify ``user`` only when the proof is about the account's OWN address.

        The single place any path is allowed to set ``User.verified_at`` from an
        OAuth link. A provider asserts one specific address; verifying the account
        on the strength of a *different* proven address would mark an address
        verified that nobody ever proved. So the canonical form of
        ``provider_email`` must equal the canonical form on the account's PRIMARY
        ``user_email`` row — anything else links the identity and leaves
        ``verified_at`` alone. Returns True when this call verified the account.
        """
        if provider_email is None or user.verified_at is not None:
            return False
        primary = (await self.db.gateway.user_email.get_primary_for_user(user.id)).value
        if primary is None:
            return False
        if await self.canonical_email(provider_email) != primary.normalized_email:
            return False
        user.verified_at = datetime.now(UTC)
        (await self.db.gateway.user.update(user)).some(RuntimeError("Failed to verify user"))
        return True

    async def email_owner_id(self, normalized_email: str) -> UUID | None:
        """The user that owns this canonical email, if any (across all accounts)."""
        row = (await self.db.gateway.user_email.get_by_normalized_email(normalized_email)).value
        return row.user_id if row is not None else None

    async def register_email(
        self,
        user_id: UUID,
        email: str,
        normalized_email: str,
        *,
        is_primary: bool = False,
        provider: IdentityProvider | None = None,
        verified: bool = False,
    ) -> Option[UserEmail]:
        """Claim a canonical email for a user in the conjoint uniqueness index.

        Idempotent for the same owner (strengthens verified/primary/provider flags
        on the existing row). Returns ``Option(None)`` when the canonical email is
        already owned by a *different* user — the caller decides whether that is a
        hard conflict (signup / email change) or an auto-link opportunity (OAuth).
        """
        existing = (
            await self.db.gateway.user_email.get_by_normalized_email(normalized_email)
        ).value
        if existing is not None:
            if existing.user_id != user_id:
                return Option(None)
            dirty = False
            if verified and existing.verified_at is None:
                existing.verified_at = datetime.now(UTC)
                dirty = True
            if is_primary and not existing.is_primary:
                existing.is_primary = True
                dirty = True
            # provider provenance is set only at creation — never overwrite it, so a
            # user's primary email row stays provider=None and is not swept away when
            # an OAuth identity reporting the same address is later unlinked.
            if dirty:
                (await self.db.gateway.user_email.update(existing)).some(
                    RuntimeError("Failed to update user email")
                )
            return Option(existing)
        row = UserEmail(
            user_id=user_id,
            email=email,
            normalized_email=normalized_email,
            is_primary=is_primary,
            provider=provider.value if provider is not None else None,
            verified_at=datetime.now(UTC) if verified else None,
        )
        return await self.db.gateway.user_email.create(row)

    def sign_email_change_token(self, user_id: UUID, canonical: str, new_email: str) -> str:
        """Sign a stateless, TTL'd email-change confirmation token.

        Emailed (as a link) to the *new* address — retrieving it there proves
        control of the new mailbox. Reuses the HMAC state signer with an ``ec|``
        prefix so it can never be confused with an OAuth state token.
        """
        return self.state_signer.generate(extra=f"ec|{user_id}|{canonical}|{new_email}")

    def verify_email_change_token(self, token: str) -> tuple[UUID, str, str] | None:
        """Return ``(user_id, canonical, new_email)`` for a valid token, else None."""
        extra = self.state_signer.verify(token, max_age=_EMAIL_CHANGE_TTL_SECONDS).value
        if extra is None:
            return None
        parts = extra.split("|")
        if len(parts) != _EMAIL_CHANGE_PARTS or parts[0] != "ec":
            return None
        try:
            user_id = UUID(parts[1])
        except ValueError:
            return None
        return user_id, parts[2], parts[3]

    async def rekey_email_password_identity(
        self, user_id: UUID, old_email: str, new_email: str
    ) -> None:
        """Point the user's EMAIL_PASSWORD login identity at the new email.

        No-op for OAuth-only users (no password identity), so email change does not
        silently break password login.
        """
        old_subject = self.normalize_subject(IdentityProvider.EMAIL_PASSWORD, old_email)
        identity = (
            await self.db.gateway.identity.get_by_provider_subject(
                IdentityProvider.EMAIL_PASSWORD, old_subject
            )
        ).value
        if identity is None or identity.user_id != user_id:
            return
        identity.provider_subject_id = self.normalize_subject(
            IdentityProvider.EMAIL_PASSWORD, new_email
        )
        (await self.db.gateway.identity.update(identity)).some(
            RuntimeError("Failed to rekey email identity")
        )

    @staticmethod
    def _token_or_none(value: str | None) -> str | None:
        """Map "no token" to NULL. An empty string is absence, not a token."""
        return value or None

    def normalize_subject(self, provider: IdentityProvider, subject_id: str) -> str:
        if provider == IdentityProvider.EMAIL_PASSWORD:
            return normalize_email(subject_id)
        if provider == IdentityProvider.USERNAME_PASSWORD:
            return normalize_username(subject_id)
        return subject_id

    async def verify_password(
        self, provider: IdentityProvider, subject_id: str, password: str
    ) -> Identity:
        if provider not in (IdentityProvider.EMAIL_PASSWORD, IdentityProvider.USERNAME_PASSWORD):
            raise AuthenticationRequiredError(
                message="Password verification not supported for this provider"
            )

        subject_id = self.normalize_subject(provider, subject_id)
        identity = (
            await self.db.gateway.identity.get_by_provider_subject(provider, subject_id)
        ).some(AuthenticationRequiredError(message="Invalid credentials"))

        if identity.credential_hash is None or not self.password_hasher.verify(
            password, identity.credential_hash
        ):
            raise AuthenticationRequiredError(message="Invalid credentials")

        return identity

    async def verify_user_password(self, user_id: UUID, password: str) -> bool:
        """True if ``password`` matches any of the user's password credentials.

        Used by the step-up reauth flow, which only has the user id (not a login
        identifier) to work with.
        """
        for identity in await self.db.gateway.identity.list_by_user_id(user_id):
            if identity.credential_hash is not None and self.password_hasher.verify(
                password, identity.credential_hash
            ):
                return True
        return False

    def initiate_oauth(self, provider: IdentityProvider, redirect_uri: str) -> InitiateResult:
        if provider in (IdentityProvider.EMAIL_PASSWORD, IdentityProvider.USERNAME_PASSWORD):
            return InitiateResult(password_prompt=True)

        adapter = self.oauth_gateway.try_get(provider)
        # An unconfigured/unregistered provider yields no redirect — the frontend
        # shows its graceful "not available" message rather than the API 500ing.
        if adapter is None:
            return InitiateResult(redirect=None)
        state = self.state_signer.generate(extra=provider.value)
        auth_url = adapter.get_authorization_url(state, redirect_uri)
        return InitiateResult(redirect=Redirect(url=auth_url.url, state=state))

    def initiate_reauth(
        self, provider: IdentityProvider, redirect_uri: str, user_id: UUID
    ) -> InitiateResult:
        """Begin a step-up OAuth challenge to re-prove a logged-in user's identity."""
        adapter = self.oauth_gateway.try_get(provider)
        if adapter is None:
            return InitiateResult(redirect=None)
        state = self.state_signer.generate(extra=f"reauth|{user_id}")
        auth_url = adapter.get_authorization_url(state, redirect_uri)
        return InitiateResult(redirect=Redirect(url=auth_url.url, state=state))

    async def verify_reauth(
        self,
        provider: IdentityProvider,
        code: str,
        state: str,
        redirect_uri: str,
        user_id: UUID,
    ) -> bool:
        """Confirm the re-OAuth round-trip resolved to an identity this user owns."""
        extra = self.state_signer.verify(state).some(
            ValidationFailedError(message="Invalid or expired OAuth state")
        )
        parts = extra.split("|")
        if len(parts) != _REAUTH_PARTS or parts[0] != "reauth" or parts[1] != str(user_id):
            return False
        adapter = self.oauth_gateway.get(provider)
        user_info = await adapter.exchange_code(code, redirect_uri)
        identity = (
            await self.db.gateway.identity.get_by_provider_subject(provider, user_info.subject_id)
        ).value
        return identity is not None and identity.user_id == user_id

    def initiate_link(
        self, provider: IdentityProvider, redirect_uri: str, user_id: UUID
    ) -> InitiateResult:
        """Begin an OAuth flow to LINK a provider to the current logged-in user."""
        adapter = self.oauth_gateway.try_get(provider)
        if adapter is None:
            return InitiateResult(redirect=None)
        state = self.state_signer.generate(extra=f"link|{user_id}")
        auth_url = adapter.get_authorization_url(state, redirect_uri)
        return InitiateResult(redirect=Redirect(url=auth_url.url, state=state))

    async def link_oauth_to_user(
        self,
        provider: IdentityProvider,
        code: str,
        state: str,
        redirect_uri: str,
        user_id: UUID,
    ) -> None:
        """Attach a provider identity to ``user_id`` — never switching accounts.

        Raises ``provider_already_linked`` when the identity already belongs to a
        different account (linking must never log you INTO that account).
        Idempotent if it is already this user's. The provider email is checked
        against the conjoint index so a link can't claim another account's email.
        """
        extra = self.state_signer.verify(state).some(
            ValidationFailedError(message="Invalid or expired OAuth state")
        )
        parts = extra.split("|")
        if len(parts) != _LINK_PARTS or parts[0] != "link" or parts[1] != str(user_id):
            raise ValidationFailedError(message="Invalid or expired OAuth state")

        adapter = self.oauth_gateway.get(provider)
        user_info = await adapter.exchange_code(code, redirect_uri)

        existing = (
            await self.db.gateway.identity.get_by_provider_subject(provider, user_info.subject_id)
        ).value
        if existing is not None:
            if existing.user_id == user_id:
                return
            raise AlreadyExistsError(
                message="This account is already connected to a different user",
                code="provider_already_linked",
            )

        email = normalize_email(user_info.email) if user_info.email else None
        canonical: str | None = None
        if email is not None:
            canonical = await self.canonical_email(email)
            owner = await self.email_owner_id(canonical)
            if owner is not None and owner != user_id:
                raise AlreadyExistsError(
                    message="That email is already used by another account",
                    code="email_taken",
                )

        await self.link_oauth_identity(user_id, user_info)
        if email is not None and canonical is not None:
            (
                await self.register_email(
                    user_id, email, canonical, provider=provider, verified=True
                )
            ).some(AlreadyExistsError(message="That email is already used", code="email_taken"))
            user = (await self.db.gateway.user.get_by_id(user_id)).some(
                AuthenticationRequiredError(message="User not found")
            )
            await self.verify_user_on_matching_email(user, email)

    async def exchange_oauth_code(
        self, provider: IdentityProvider, code: str, state: str, redirect_uri: str
    ) -> tuple[Identity | None, OAuthUserInfo]:
        verified_extra = self.state_signer.verify(state).some(
            ValidationFailedError(message="Invalid or expired OAuth state")
        )
        # A step-up (reauth/link) state must never drive a login/signup — that is
        # exactly the account-switch a malicious replay would attempt.
        if verified_extra.split("|", 1)[0] in _STEP_UP_PREFIXES:
            raise ValidationFailedError(message="Invalid or expired OAuth state")

        adapter = self.oauth_gateway.get(provider)
        user_info = await adapter.exchange_code(code, redirect_uri)

        existing = await self.db.gateway.identity.get_by_provider_subject(
            provider, user_info.subject_id
        )

        if existing.value is not None:
            identity = existing.value
            identity.access_token_enc = self._token_or_none(user_info.access_token)
            identity.refresh_token_enc = self._token_or_none(user_info.refresh_token)
            identity.provider_email = user_info.email
            identity.provider_display_name = user_info.display_name
            identity.provider_avatar_url = user_info.avatar_url
            identity.scopes = user_info.scopes
            (await self.db.gateway.identity.update(identity)).some(
                RuntimeError("Failed to update identity")
            )
            return identity, user_info

        return None, user_info

    async def link_oauth_identity(self, user_id: UUID, user_info: OAuthUserInfo) -> Identity:
        provider_email = normalize_email(user_info.email) if user_info.email else None
        identity = Identity(
            user_id=user_id,
            provider=user_info.provider,
            provider_subject_id=user_info.subject_id,
            access_token_enc=self._token_or_none(user_info.access_token),
            refresh_token_enc=self._token_or_none(user_info.refresh_token),
            provider_email=provider_email,
            provider_display_name=user_info.display_name,
            provider_avatar_url=user_info.avatar_url,
            scopes=user_info.scopes,
        )
        return (await self.db.gateway.identity.create(identity)).some(
            RuntimeError("Failed to create identity")
        )

    async def link_password_identity(
        self, user_id: UUID, provider: IdentityProvider, subject_id: str, password: str
    ) -> Identity:
        subject_id = self.normalize_subject(provider, subject_id)
        identity = Identity(
            user_id=user_id,
            provider=provider,
            provider_subject_id=subject_id,
            credential_hash=self.password_hasher.hash(password),
        )
        return (await self.db.gateway.identity.create(identity)).some(
            RuntimeError("Failed to create identity")
        )

    async def set_password_identity(
        self, user_id: UUID, provider: IdentityProvider, subject_id: str, password: str
    ) -> Identity:
        """Upsert a password identity.

        Updates the credential hash if the identity already exists, otherwise
        creates it. Used by the forgot-password flow, where the target account may
        or may not already carry a password identity for this provider/subject.
        """
        subject_id = self.normalize_subject(provider, subject_id)
        existing = (
            await self.db.gateway.identity.get_by_provider_subject(provider, subject_id)
        ).value
        if existing is not None:
            existing.credential_hash = self.password_hasher.hash(password)
            return (await self.db.gateway.identity.update(existing)).some(
                RuntimeError("Failed to update identity")
            )
        return await self.link_password_identity(user_id, provider, subject_id, password)

    async def get_identities_for_user(self, user_id: UUID) -> list[Identity]:
        return await self.db.gateway.identity.list_by_user_id(user_id)
