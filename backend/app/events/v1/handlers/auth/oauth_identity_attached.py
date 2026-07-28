from dataclasses import dataclass

from backend.app.events.v1.handlers.base import EventHandler
from backend.app.shared.events.v1.oauth_identity_attached import OAuthIdentityAttached
from backend.app.shared.ports.outreach.email import EmailSender, EmailType


@dataclass
class OAuthIdentityAttachedHandler(EventHandler[OAuthIdentityAttached]):
    email_sender: EmailSender

    async def __call__(self, event: OAuthIdentityAttached, /) -> None:
        # Only a user with a deliverable address gets the security notice.
        if event.email is None:
            return
        await self.email_sender.send(
            to=event.email,
            type=EmailType.SIGN_IN_METHOD_ADDED,
            params={"username": event.username, "provider": event.provider},
        )
