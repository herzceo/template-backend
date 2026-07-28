from dataclasses import dataclass
from datetime import UTC, datetime

from backend.app.errors import ValidationFailedError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.dtos.auth import AuthContext
from backend.app.rest.v1.handlers.auth._common import resolve_user_by_identifier
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.session import SessionService
from backend.app.rest.v1.services.types import ClientDeviceInfo
from backend.app.shared.db.database import Database
from backend.app.shared.ports.security.login_code import LoginCodeStore
from backend.app.shared.ports.security.verification import VerificationEntry

# One identical message whether the account is unknown OR exists-but-has-no-pending
# code — so this endpoint can't be used to tell the two apart (matches the
# enumeration-safe neutrality of its sibling loginCodeRequest).
_NO_PENDING = "No pending login code"


class LoginCodeVerifyCommand(Command):
    identifier: str
    code: str
    ip: str | None = None
    user_agent: str | None = None
    client_device: ClientDeviceInfo | None = None


@dataclass
class VerifyLoginCodeHandler(
    Handler[LoginCodeVerifyCommand, AuthContext[dtos.User], None], type_=HandlerType.WRITE
):
    db: Database
    session_service: SessionService
    login_code_store: LoginCodeStore

    async def __call__(
        self, cmd: LoginCodeVerifyCommand, _ctx: None = None
    ) -> AuthContext[dtos.User]:
        user = (await resolve_user_by_identifier(self.db, cmd.identifier)).some(
            ValidationFailedError(message=_NO_PENDING)
        )
        user_id = user.id

        entry = (await self.login_code_store.get(user_id)).some(
            ValidationFailedError(message=_NO_PENDING)
        )

        if entry.attempts >= self.login_code_store.max_attempts:
            raise self._too_many_attempts(entry)

        if not await self.login_code_store.verify(user_id, cmd.code):
            updated = (await self.login_code_store.get(user_id)).value
            remaining = self.login_code_store.max_attempts - (updated.attempts if updated else 0)
            if remaining <= 0:
                raise self._too_many_attempts(updated or entry)
            raise ValidationFailedError(message=f"Invalid code, {remaining} attempt(s) remaining")

        if not user.is_verified:
            raise ValidationFailedError(message="Email not verified")

        raw_token, _ = await self.session_service.create_session(
            user_id,
            ip=cmd.ip,
            user_agent=cmd.user_agent,
            client_device=cmd.client_device,
        )
        return AuthContext(token=raw_token, data=dtos.User.from_object(user))

    def _too_many_attempts(self, entry: VerificationEntry) -> ValidationFailedError:
        details: dict[str, str] = {}
        if entry.created_at:
            try:
                issued_at = datetime.fromisoformat(entry.created_at)
            except ValueError:
                issued_at = None
            if issued_at is not None:
                elapsed = (datetime.now(UTC) - issued_at).total_seconds()
                remaining = max(0, int(self.login_code_store.ttl_seconds - elapsed))
                details["retry_after_seconds"] = str(remaining)
        return ValidationFailedError(
            message="Too many attempts, request a new code",
            details=details,
        )
