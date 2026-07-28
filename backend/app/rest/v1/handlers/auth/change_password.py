from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import AuthenticationRequiredError, NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.validation import validate_password
from backend.app.shared.db.database import Database
from backend.app.shared.ports.security.login_code import LoginCodeStore
from backend.app.shared.ports.security.one_time_token import (
    OTT_PURPOSE_REAUTH,
    OneTimeTokenStore,
)
from backend.app.shared.ports.security.verification import VerificationCodeStore
from backend.domain.enums import IdentityProvider


class ChangePasswordCommand(Command):
    user_id: UUID
    reauth_token: str
    new_password: str


@dataclass
class ChangePasswordHandler(
    Handler[ChangePasswordCommand, dtos.User, None], type_=HandlerType.WRITE
):
    db: Database
    identity_service: IdentityService
    ott_store: OneTimeTokenStore
    login_code_store: LoginCodeStore
    verification_store: VerificationCodeStore

    async def __call__(self, cmd: ChangePasswordCommand, _ctx: None = None) -> dtos.User:
        reauth_user = (await self.ott_store.consume(OTT_PURPOSE_REAUTH, cmd.reauth_token)).some(
            AuthenticationRequiredError(message="Re-authentication required")
        )
        if reauth_user != cmd.user_id:
            raise AuthenticationRequiredError(message="Re-authentication required")
        validate_password(cmd.new_password)

        async with self.db:
            user = (await self.db.gateway.user.get_by_id(cmd.user_id)).some(NotFoundError())
            await self.identity_service.set_password_identity(
                cmd.user_id, IdentityProvider.USERNAME_PASSWORD, user.username, cmd.new_password
            )
            if user.email is not None:
                await self.identity_service.set_password_identity(
                    cmd.user_id, IdentityProvider.EMAIL_PASSWORD, user.email, cmd.new_password
                )
            # Force re-login everywhere: a password change revokes all existing
            # sessions (including this one) so a compromised session can't persist.
            await self.db.gateway.session_.delete_by_user_id(cmd.user_id)
            await self.db.commit()

        # Drop any pending login/verification code issued before the change.
        await self.login_code_store.invalidate(cmd.user_id)
        await self.verification_store.invalidate(cmd.user_id)
        return dtos.User.from_object(user)
