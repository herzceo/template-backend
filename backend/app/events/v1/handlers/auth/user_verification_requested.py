from dataclasses import dataclass

from backend.app.events.v1.handlers.base import EventHandler
from backend.app.ports.email import EmailSender, EmailType
from backend.app.ports.verification import VerificationCodeStore
from backend.app.shared.events.v1.user_verification_requested import UserVerificationRequested


@dataclass
class UserVerificationRequestedHandler(EventHandler[UserVerificationRequested]):
    email_sender: EmailSender
    verification_store: VerificationCodeStore

    async def __call__(self, event: UserVerificationRequested, /) -> None:
        raw_code = await self.verification_store.issue_code(event.user_id)

        await self.email_sender.send(
            to=event.email,
            type=EmailType.EMAIL_VERIFICATION,
            params={"username": event.username, "code": raw_code},
        )
