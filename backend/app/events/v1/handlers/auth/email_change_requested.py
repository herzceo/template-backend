from dataclasses import dataclass

from backend.app.events.v1.handlers.base import EventHandler
from backend.app.shared.events.v1.email_change_requested import EmailChangeRequested
from backend.app.shared.ports.outreach.email import EmailSender, EmailType


@dataclass
class EmailChangeRequestedHandler(EventHandler[EmailChangeRequested]):
    email_sender: EmailSender

    async def __call__(self, event: EmailChangeRequested, /) -> None:
        await self.email_sender.send(
            to=event.new_email,
            type=EmailType.EMAIL_CHANGE_VERIFICATION,
            params={"username": event.username, "confirm_url": event.confirm_url},
        )
