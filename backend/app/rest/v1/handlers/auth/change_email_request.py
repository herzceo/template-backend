from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import (
    AlreadyExistsError,
    AuthenticationRequiredError,
    NotFoundError,
    ValidationFailedError,
)
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.app_config import AppConfig, RateLimitConfig
from backend.app.rest.v1.handlers.auth._common import enforce_rate_limit
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.validation import normalize_email
from backend.app.shared.db.database import Database
from backend.app.shared.events.v1.email_change_requested import EmailChangeRequested
from backend.app.shared.ports.security.one_time_token import (
    OTT_PURPOSE_REAUTH,
    OneTimeTokenStore,
)
from backend.app.shared.ports.security.rate_limiter import RateLimiter


class ChangeEmailRequestCommand(Command):
    user_id: UUID
    reauth_token: str
    new_email: str
    ip: str | None = None


@dataclass
class ChangeEmailRequestHandler(
    Handler[ChangeEmailRequestCommand, dtos.DeliveryAck, None], type_=HandlerType.WRITE
):
    db: Database
    identity_service: IdentityService
    ott_store: OneTimeTokenStore
    config: AppConfig
    rate_limiter: RateLimiter
    rate_config: RateLimitConfig

    async def __call__(self, cmd: ChangeEmailRequestCommand, _ctx: None = None) -> dtos.DeliveryAck:
        await enforce_rate_limit(
            self.rate_limiter,
            cmd.ip and f"change_email:{cmd.ip}",
            limit=self.rate_config.AUTH_RATE_LIMIT,
            window_seconds=self.rate_config.AUTH_RATE_WINDOW_SECONDS,
        )
        reauth_user = (await self.ott_store.consume(OTT_PURPOSE_REAUTH, cmd.reauth_token)).some(
            AuthenticationRequiredError(message="Re-authentication required")
        )
        if reauth_user != cmd.user_id:
            raise AuthenticationRequiredError(message="Re-authentication required")

        email = normalize_email(cmd.new_email)
        canonical = await self.identity_service.canonical_email(email)

        async with self.db:
            user = (await self.db.gateway.user.get_by_id(cmd.user_id)).some(NotFoundError())
            owner = await self.identity_service.email_owner_id(canonical)
            if owner == cmd.user_id:
                raise ValidationFailedError(message="That's already your email")
            if owner is not None:
                raise AlreadyExistsError(
                    message="This email is already registered", code="email_taken"
                )

            token = self.identity_service.sign_email_change_token(cmd.user_id, canonical, email)
            confirm_url = f"{self.config.public_base}/settings/confirm-email?token={token}"
            await self.db.dbus.publish(
                EmailChangeRequested(
                    user_id=cmd.user_id,
                    new_email=email,
                    username=user.username,
                    confirm_url=confirm_url,
                )
            )
            await self.db.commit()

        return dtos.DeliveryAck()
