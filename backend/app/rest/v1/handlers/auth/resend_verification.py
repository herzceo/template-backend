from dataclasses import dataclass
from datetime import UTC, datetime

from backend.app.errors import ValidationFailedError
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.events.v1.user_verification_requested import UserVerificationRequested
from backend.app.shared.ports.events.dbus import DBus
from backend.app.shared.ports.security.verification import VerificationCodeStore
from backend.domain.repos.database import Database

RESEND_COOLDOWN_SECONDS = 60


class ResendVerificationCommand(Command):
    email: str


@dataclass
class ResendVerificationHandler(
    Handler[ResendVerificationCommand, None, None], type_=HandlerType.WRITE
):
    db: Database
    dbus: DBus
    verification_store: VerificationCodeStore

    async def __call__(self, cmd: ResendVerificationCommand, _ctx: None = None) -> None:
        async with self.db:
            user = (await self.db.gateway.user.get_by_email(cmd.email)).some(
                ValidationFailedError(message="Invalid email")
            )

        if user.is_verified:
            raise ValidationFailedError(message="Email already verified")

        entry = (await self.verification_store.get(user.id)).value
        if entry is not None:
            elapsed = (datetime.now(UTC) - datetime.fromisoformat(entry.created_at)).total_seconds()
            if elapsed < RESEND_COOLDOWN_SECONDS:
                wait = int(RESEND_COOLDOWN_SECONDS - elapsed)
                raise ValidationFailedError(
                    message=f"Please wait {wait} seconds before requesting a new code"
                )

        await self.dbus.publish(
            UserVerificationRequested(
                user_id=user.id,
                email=user.email,
                username=user.username,
            )
        )
