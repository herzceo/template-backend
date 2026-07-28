from dataclasses import dataclass

from backend.app.events.v1.handlers.base import EventHandler
from backend.app.shared.events.v1.oauth_signup_verification_requested import (
    OAuthSignupVerificationRequested,
)
from backend.app.shared.ports.outreach.email import EmailSender, EmailType
from backend.app.shared.ports.security.verification import VerificationCodeStore


@dataclass
class OAuthSignupVerificationRequestedHandler(EventHandler[OAuthSignupVerificationRequested]):
    """Mail the signup code for an account that does not exist yet.

    The code is keyed on the setup session id, not a user id — there is no user
    yet. It reuses the standard email-verification template.
    """

    email_sender: EmailSender
    verification_store: VerificationCodeStore

    async def __call__(self, event: OAuthSignupVerificationRequested, /) -> None:
        raw_code = await self.verification_store.issue_code(event.setup_id)
        await self.email_sender.send(
            to=event.email,
            type=EmailType.EMAIL_VERIFICATION,
            params={"username": event.username, "code": raw_code},
        )
