from dataclasses import dataclass

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.app_config import AppConfig, RateLimitConfig
from backend.app.rest.v1.handlers.auth._common import enforce_rate_limit, resolve_user_by_identifier
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database
from backend.app.shared.events.v1.password_reset_requested import PasswordResetRequested
from backend.app.shared.ports.security.one_time_token import (
    OTT_PURPOSE_PASSWORD_RESET,
    OneTimeTokenStore,
)
from backend.app.shared.ports.security.rate_limiter import RateLimiter

# Reset-link lifetime — longer than the login/verify codes because it lands in an
# inbox and the user may act on it later.
PASSWORD_RESET_TTL_SECONDS = 60 * 60


class PasswordResetRequestCommand(Command):
    identifier: str
    ip: str | None = None


@dataclass
class RequestPasswordResetHandler(
    Handler[PasswordResetRequestCommand, dtos.DeliveryAck, None], type_=HandlerType.WRITE
):
    db: Database
    ott_store: OneTimeTokenStore
    config: AppConfig
    rate_limiter: RateLimiter
    rate_config: RateLimitConfig

    async def __call__(
        self, cmd: PasswordResetRequestCommand, _ctx: None = None
    ) -> dtos.DeliveryAck:
        await enforce_rate_limit(
            self.rate_limiter,
            cmd.ip and f"password_reset:{cmd.ip}",
            limit=self.rate_config.AUTH_RATE_LIMIT,
            window_seconds=self.rate_config.AUTH_RATE_WINDOW_SECONDS,
        )
        user = (await resolve_user_by_identifier(self.db, cmd.identifier)).value

        # Only mint a reset link for a real account with an address; always answer
        # the same so the response never reveals whether the account exists.
        if user is not None and user.email is not None:
            token = await self.ott_store.issue(
                OTT_PURPOSE_PASSWORD_RESET, user.id, PASSWORD_RESET_TTL_SECONDS
            )
            reset_url = f"{self.config.public_base}/reset-password?token={token}"
            async with self.db:
                await self.db.dbus.publish(
                    PasswordResetRequested(
                        user_id=user.id,
                        email=user.email,
                        username=user.username,
                        reset_url=reset_url,
                    )
                )
                await self.db.commit()

        return dtos.DeliveryAck()
