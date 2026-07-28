from dataclasses import dataclass

from backend.app.events.v1.handlers.base import EventHandler
from backend.app.shared.events.v1.login_code_requested import LoginCodeRequested
from backend.app.shared.ports.outreach.email import EmailSender, EmailType
from backend.app.shared.ports.security.login_code import LoginCodeStore


@dataclass
class LoginCodeRequestedHandler(EventHandler[LoginCodeRequested]):
    email_sender: EmailSender
    login_code_store: LoginCodeStore

    async def __call__(self, event: LoginCodeRequested, /) -> None:
        raw_code = await self.login_code_store.issue_code(event.user_id)
        await self.email_sender.send(
            to=event.email,
            type=EmailType.LOGIN_CODE,
            params={"username": event.username, "code": raw_code},
        )
