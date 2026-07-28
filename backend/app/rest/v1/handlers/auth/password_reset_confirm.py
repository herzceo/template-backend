from dataclasses import dataclass
from datetime import UTC, datetime

from backend.app.errors import ValidationFailedError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.dtos.auth import AuthContext
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.services.session import SessionService
from backend.app.rest.v1.services.types import ClientDeviceInfo
from backend.app.rest.v1.validation import validate_password
from backend.app.shared.db.database import Database
from backend.app.shared.ports.security.login_code import LoginCodeStore
from backend.app.shared.ports.security.one_time_token import (
    OTT_PURPOSE_PASSWORD_RESET,
    OneTimeTokenStore,
)
from backend.app.shared.ports.security.verification import VerificationCodeStore
from backend.domain.enums import IdentityProvider


class PasswordResetConfirmCommand(Command):
    token: str
    password: str
    ip: str | None = None
    user_agent: str | None = None
    client_device: ClientDeviceInfo | None = None


@dataclass
class ConfirmPasswordResetHandler(
    Handler[PasswordResetConfirmCommand, AuthContext[dtos.User], None], type_=HandlerType.WRITE
):
    db: Database
    session_service: SessionService
    identity_service: IdentityService
    ott_store: OneTimeTokenStore
    login_code_store: LoginCodeStore
    verification_store: VerificationCodeStore

    async def __call__(
        self, cmd: PasswordResetConfirmCommand, _ctx: None = None
    ) -> AuthContext[dtos.User]:
        user_id = (await self.ott_store.consume(OTT_PURPOSE_PASSWORD_RESET, cmd.token)).some(
            ValidationFailedError(message="This reset link is invalid or has expired.")
        )
        validate_password(cmd.password)

        async with self.db:
            user = (await self.db.gateway.user.get_by_id(user_id)).some(
                ValidationFailedError(message="This reset link is invalid or has expired.")
            )
            email = user.email
            username = user.username

            # A valid reset link proves email ownership — verify the account if it
            # wasn't already (e.g. reset requested before finishing signup).
            if user.verified_at is None:
                user.verified_at = datetime.now(UTC)
                (await self.db.gateway.user.update(user)).some(
                    RuntimeError("Failed to verify user")
                )

            if email is not None:
                await self.identity_service.set_password_identity(
                    user_id, IdentityProvider.EMAIL_PASSWORD, email, cmd.password
                )
            await self.identity_service.set_password_identity(
                user_id, IdentityProvider.USERNAME_PASSWORD, username, cmd.password
            )
            # Revoke every existing session — a stolen/attacker session must not
            # survive the victim resetting their password.
            await self.db.gateway.session_.delete_by_user_id(user_id)
            await self.db.commit()

        # Drop any pending login/verification code so one issued before the reset
        # can't still be redeemed afterwards.
        await self.login_code_store.invalidate(user_id)
        await self.verification_store.invalidate(user_id)

        raw_token, _ = await self.session_service.create_session(
            user_id,
            ip=cmd.ip,
            user_agent=cmd.user_agent,
            client_device=cmd.client_device,
        )
        return AuthContext(token=raw_token, data=dtos.User.from_object(user))
