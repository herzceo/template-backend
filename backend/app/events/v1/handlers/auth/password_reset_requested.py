from dataclasses import dataclass

from backend.app.events.v1.handlers.base import EventHandler
from backend.app.shared.events.v1.password_reset_requested import PasswordResetRequested
from backend.app.shared.ports.outreach.email import EmailSender, EmailType


@dataclass
class PasswordResetRequestedHandler(EventHandler[PasswordResetRequested]):
    email_sender: EmailSender

    async def __call__(self, event: PasswordResetRequested, /) -> None:
        await self.email_sender.send(
            to=event.email,
            type=EmailType.PASSWORD_RESET,
            params={"username": event.username, "reset_url": event.reset_url},
        )
