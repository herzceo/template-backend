from typing import Literal, final

from backend.app.ports.email import EmailSender, EmailType, VerificationEmailParams
from backend.infra.external.http.resend.client import ResendClient

_TEMPLATES: dict[EmailType, tuple[str, str]] = {
    EmailType.EMAIL_VERIFICATION: (
        "Verify your email",
        (
            "<p>Hi {username},</p>"
            "<p>Your verification code is: <strong>{code}</strong></p>"
            "<p>This code expires in 15 minutes.</p>"
        ),
    ),
}


@final
class ImplResendEmailSender(EmailSender):
    __slots__ = ("_client", "_from_email")

    def __init__(self, client: ResendClient, from_email: str) -> None:
        self._client = client
        self._from_email = from_email

    async def send(
        self,
        *,
        to: str,
        type: Literal[EmailType.EMAIL_VERIFICATION],
        params: VerificationEmailParams,
    ) -> None:
        subject_template, html_template = _TEMPLATES[type]
        await self._client.send(
            from_=self._from_email,
            to=[to],
            subject=subject_template.format(**params),
            html=html_template.format(**params),
        )
