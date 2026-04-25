from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import AuthenticationRequiredError, ValidationFailedError
from backend.app.rest.v1.dtos.identity import (
    InitiateResult,
    Redirect,
)
from backend.app.shared.ports.auth.oauth_gateway import OAuthGateway, OAuthUserInfo
from backend.app.shared.ports.auth.oauth_state import OAuthStateSigner
from backend.app.shared.ports.auth.password_hasher import PasswordHasher
from backend.domain.entities.identity import Identity
from backend.domain.enums import IdentityProvider
from backend.domain.repos.database import Database


@dataclass
class IdentityService:
    db: Database
    password_hasher: PasswordHasher
    oauth_gateway: OAuthGateway
    state_signer: OAuthStateSigner

    async def verify_password(
        self, provider: IdentityProvider, subject_id: str, password: str
    ) -> Identity:
        if provider not in (IdentityProvider.EMAIL_PASSWORD, IdentityProvider.USERNAME_PASSWORD):
            raise AuthenticationRequiredError(
                message="Password verification not supported for this provider"
            )

        identity = (
            await self.db.gateway.identity.get_by_provider_subject(provider, subject_id)
        ).some(AuthenticationRequiredError(message="Invalid credentials"))

        if identity.credential_hash is None or not self.password_hasher.verify(
            password, identity.credential_hash
        ):
            raise AuthenticationRequiredError(message="Invalid credentials")

        return identity

    def initiate_oauth(self, provider: IdentityProvider) -> InitiateResult:
        if provider in (IdentityProvider.EMAIL_PASSWORD, IdentityProvider.USERNAME_PASSWORD):
            return InitiateResult(password_prompt=True)

        adapter = self.oauth_gateway.get(provider)
        state = self.state_signer.generate(extra=provider)
        auth_url = adapter.get_authorization_url(state)
        return InitiateResult(redirect=Redirect(url=auth_url.url, state=state))

    async def exchange_oauth_code(
        self, provider: IdentityProvider, code: str, state: str
    ) -> tuple[Identity | None, OAuthUserInfo]:
        self.state_signer.verify(state).some(
            ValidationFailedError(message="Invalid or expired OAuth state")
        )

        adapter = self.oauth_gateway.get(provider)
        user_info = await adapter.exchange_code(code)

        existing = await self.db.gateway.identity.get_by_provider_subject(
            provider, user_info.subject_id
        )

        if existing.value is not None:
            identity = existing.value
            identity.access_token_enc = user_info.access_token
            identity.refresh_token_enc = user_info.refresh_token
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
        identity = Identity(
            user_id=user_id,
            provider=user_info.provider,
            provider_subject_id=user_info.subject_id,
            access_token_enc=user_info.access_token,
            refresh_token_enc=user_info.refresh_token,
            provider_email=user_info.email,
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
        identity = Identity(
            user_id=user_id,
            provider=provider,
            provider_subject_id=subject_id,
            credential_hash=self.password_hasher.hash(password),
        )
        return (await self.db.gateway.identity.create(identity)).some(
            RuntimeError("Failed to create identity")
        )

    async def get_identities_for_user(self, user_id: UUID) -> list[Identity]:
        return await self.db.gateway.identity.list_by_user_id(user_id)
