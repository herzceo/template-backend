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
from backend.app.shared.ports.security.one_time_token import (
    OTT_PURPOSE_SIGNUP_SETUP,
    OneTimeTokenStore,
)
from backend.domain.enums import IdentityProvider


class SetPasswordCommand(Command):
    setup_token: str
    password: str
    ip: str | None = None
    user_agent: str | None = None
    client_device: ClientDeviceInfo | None = None


@dataclass
class SetPasswordHandler(
    Handler[SetPasswordCommand, AuthContext[dtos.User], None], type_=HandlerType.WRITE
):
    db: Database
    session_service: SessionService
    identity_service: IdentityService
    ott_store: OneTimeTokenStore

    async def __call__(self, cmd: SetPasswordCommand, _ctx: None = None) -> AuthContext[dtos.User]:
        user_id = (await self.ott_store.consume(OTT_PURPOSE_SIGNUP_SETUP, cmd.setup_token)).some(
            ValidationFailedError(message="This signup session expired — start again.")
        )
        validate_password(cmd.password)

        async with self.db:
            user = (await self.db.gateway.user.get_by_id(user_id)).some(
                ValidationFailedError(message="This signup session expired — start again.")
            )
            email = user.email
            username = user.username

            user.verified_at = datetime.now(UTC)
            (await self.db.gateway.user.update(user)).some(RuntimeError("Failed to verify user"))

            # The account is now real: mark its primary email verified in the
            # conjoint uniqueness index (created unverified at signup).
            primary_email = (await self.db.gateway.user_email.get_primary_for_user(user_id)).value
            if primary_email is not None and primary_email.verified_at is None:
                primary_email.verified_at = datetime.now(UTC)
                (await self.db.gateway.user_email.update(primary_email)).some(
                    RuntimeError("Failed to verify user email")
                )

            if email is not None:
                await self.identity_service.link_password_identity(
                    user_id, IdentityProvider.EMAIL_PASSWORD, email, cmd.password
                )
            await self.identity_service.link_password_identity(
                user_id, IdentityProvider.USERNAME_PASSWORD, username, cmd.password
            )
            await self.db.commit()

        raw_token, _ = await self.session_service.create_session(
            user_id,
            ip=cmd.ip,
            user_agent=cmd.user_agent,
            client_device=cmd.client_device,
        )
        return AuthContext(token=raw_token, data=dtos.User.from_object(user))
