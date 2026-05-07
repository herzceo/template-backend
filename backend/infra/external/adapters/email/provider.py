from pathlib import Path
from typing import Literal, final

import jinja2

from backend.app.shared.ports.outreach.email import EmailSender, EmailType, VerificationEmailParams
from backend.infra.external.http.resend.client import ResendClient

_SUBJECTS: dict[EmailType, str] = {
    EmailType.EMAIL_VERIFICATION: "Verify your email",
}


@final
class ImplResendEmailSender(EmailSender):
    __slots__ = ("_client", "_env", "_from_email")

    def __init__(self, client: ResendClient, from_email: str) -> None:
        self._client = client
        self._from_email = from_email
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
            autoescape=jinja2.select_autoescape(["html"]),
        )

    async def send(
        self,
        *,
        to: str,
        type: Literal[EmailType.EMAIL_VERIFICATION],
        params: VerificationEmailParams,
    ) -> None:
        template = self._env.get_template(f"{type}.html")
        await self._client.send(
            from_=self._from_email,
            to=[to],
            subject=_SUBJECTS[type],
            html=template.render(**params),
        )
