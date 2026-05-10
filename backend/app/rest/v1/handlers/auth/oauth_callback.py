from dataclasses import dataclass

from backend.app.errors import AuthenticationRequiredError, NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.dtos.auth import AuthContext
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.services.session import SessionService
from backend.app.rest.v1.validation import normalize_email, sanitize_username_chars
from backend.domain.entities.profile import Profile
from backend.domain.entities.user import User
from backend.domain.enums import IdentityProvider
from backend.domain.repos.database import Database


class OAuthCallbackCommand(Command):
    provider: IdentityProvider
    code: str
    state: str


@dataclass
class OAuthCallbackHandler(
    Handler[OAuthCallbackCommand, AuthContext[dtos.User], None],
    type_=HandlerType.WRITE,
):
    db: Database
    identity_service: IdentityService
    session_service: SessionService

    async def __call__(
        self, cmd: OAuthCallbackCommand, _ctx: None = None
    ) -> AuthContext[dtos.User]:
        async with self.db:
            identity, user_info = await self.identity_service.exchange_oauth_code(
                cmd.provider, cmd.code, cmd.state
            )

            if identity is not None:
                user = (await self.db.gateway.user.get_by_id(identity.user_id)).some(
                    AuthenticationRequiredError(message="User not found")
                )
            else:
                default_tenant = (await self.db.gateway.tenant.get_default()).some(
                    NotFoundError(message="No default tenant configured")
                )

                username = self._build_username(
                    cmd.provider, user_info.subject_id, user_info.display_name
                )
                email = normalize_email(user_info.email) if user_info.email else None

                user_entity = User(
                    username=username,
                    email=email,
                    tenant_id=default_tenant.id,
                )
                user = (await self.db.gateway.user.create(user_entity)).some(
                    RuntimeError("Failed to create user")
                )
                profile = Profile(
                    user_id=user.id,
                    display_name=user_info.display_name,
                    avatar_url=user_info.avatar_url,
                )
                (await self.db.gateway.profile.create(profile)).some(
                    RuntimeError("Failed to create profile")
                )
                await self.identity_service.link_oauth_identity(user.id, user_info)

            raw_token, _ = await self.session_service.create_session(user.id)
            await self.db.commit()

        return AuthContext(token=raw_token, data=dtos.User.from_object(user))

    @staticmethod
    def _build_username(
        provider: IdentityProvider, subject_id: str, display_name: str | None
    ) -> str:
        if display_name:
            safe = sanitize_username_chars(display_name)
            return f"{safe}_{provider}_{subject_id}"
        return f"{provider}_{subject_id}"
