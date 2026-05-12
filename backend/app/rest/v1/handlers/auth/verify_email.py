from dataclasses import dataclass
from datetime import UTC, datetime

from backend.app.errors import ValidationFailedError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.dtos.auth import AuthContext
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.session import SessionService
from backend.app.rest.v1.services.types import ClientDeviceInfo
from backend.app.rest.v1.validation import normalize_email
from backend.app.shared.db.database import Database
from backend.app.shared.ports.security.verification import VerificationCodeStore


class VerifyEmailCommand(Command):
    email: str
    code: str
    ip: str | None = None
    user_agent: str | None = None
    client_device: ClientDeviceInfo | None = None


@dataclass
class VerifyEmailHandler(
    Handler[VerifyEmailCommand, AuthContext[dtos.User], None], type_=HandlerType.WRITE
):
    db: Database
    session_service: SessionService
    verification_store: VerificationCodeStore

    async def __call__(self, cmd: VerifyEmailCommand, _ctx: None = None) -> AuthContext[dtos.User]:
        email = normalize_email(cmd.email)

        async with self.db:
            user = (await self.db.gateway.user.get_by_email(email)).some(
                ValidationFailedError(message="Invalid email or code")
            )
            user_id = user.id

        entry = (await self.verification_store.get(user_id)).some(
            ValidationFailedError(message="No pending verification")
        )

        if entry.attempts >= self.verification_store.max_attempts:
            raise ValidationFailedError(message="Too many attempts, request a new code")

        if not await self.verification_store.verify(user_id, cmd.code):
            updated = (await self.verification_store.get(user_id)).value
            remaining = self.verification_store.max_attempts - (updated.attempts if updated else 0)
            if remaining <= 0:
                raise ValidationFailedError(message="Too many attempts, request a new code")
            raise ValidationFailedError(message=f"Invalid code, {remaining} attempt(s) remaining")

        async with self.db:
            user = (await self.db.gateway.user.get_by_id(user_id)).some(
                ValidationFailedError(message="Invalid email or code")
            )
            user.verified_at = datetime.now(UTC)
            (await self.db.gateway.user.update(user)).some(RuntimeError("Failed to verify user"))
            await self.db.commit()

        raw_token, _ = await self.session_service.create_session(
            user_id,
            ip=cmd.ip,
            user_agent=cmd.user_agent,
            client_device=cmd.client_device,
        )
        return AuthContext(token=raw_token, data=dtos.User.from_object(user))
