from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.app_config import RateLimitConfig
from backend.app.rest.v1.handlers.auth._common import enforce_rate_limit, resolve_user_by_identifier
from backend.app.rest.v1.handlers.auth.resend_verification import RESEND_COOLDOWN_SECONDS
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database
from backend.app.shared.events.v1.login_code_requested import LoginCodeRequested
from backend.app.shared.ports.security.login_code import LoginCodeStore
from backend.app.shared.ports.security.rate_limiter import RateLimiter


class LoginCodeRequestCommand(Command):
    identifier: str
    ip: str | None = None


@dataclass
class RequestLoginCodeHandler(
    Handler[LoginCodeRequestCommand, dtos.DeliveryAck, None], type_=HandlerType.WRITE
):
    db: Database
    login_code_store: LoginCodeStore
    rate_limiter: RateLimiter
    rate_config: RateLimitConfig

    async def __call__(self, cmd: LoginCodeRequestCommand, _ctx: None = None) -> dtos.DeliveryAck:
        # Throttle per IP before any lookup — enumeration-safe and stops email-bombing.
        await enforce_rate_limit(
            self.rate_limiter,
            cmd.ip and f"login_code:{cmd.ip}",
            limit=self.rate_config.AUTH_RATE_LIMIT,
            window_seconds=self.rate_config.AUTH_RATE_WINDOW_SECONDS,
        )
        # Enumeration-safe: the response is byte-identical whether or not an
        # account exists. A code is queued only for a verified account with an
        # address, and only when it is not still within the resend cooldown — but
        # the caller learns none of that.
        user = (await resolve_user_by_identifier(self.db, cmd.identifier)).value
        if (
            user is not None
            and user.is_verified
            and user.email is not None
            and not self._within_cooldown(await self._issued_at(user.id))
        ):
            async with self.db:
                await self.db.dbus.publish(
                    LoginCodeRequested(user_id=user.id, email=user.email, username=user.username)
                )
                await self.db.commit()
        return dtos.DeliveryAck()

    async def _issued_at(self, user_id: UUID) -> datetime | None:
        entry = (await self.login_code_store.get(user_id)).value
        if entry is None or not entry.created_at:
            return None
        try:
            return datetime.fromisoformat(entry.created_at)
        except ValueError:
            return None

    @staticmethod
    def _within_cooldown(issued_at: datetime | None) -> bool:
        if issued_at is None:
            return False
        elapsed = (datetime.now(UTC) - issued_at).total_seconds()
        return elapsed < RESEND_COOLDOWN_SECONDS
