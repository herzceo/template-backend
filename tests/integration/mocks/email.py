from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, final

if TYPE_CHECKING:
    from backend.app.shared.ports.outreach.email import EmailType, VerificationEmailParams


@dataclass
class SentEmail:
    to: str
    type: EmailType
    params: VerificationEmailParams


@final
@dataclass
class MockEmailSender:
    _sent: list[SentEmail] = field(default_factory=list)

    async def send(
        self,
        *,
        to: str,
        type: Literal[EmailType.EMAIL_VERIFICATION],
        params: VerificationEmailParams,
    ) -> None:
        self._sent.append(SentEmail(to=to, type=type, params=params))

    def get_sent(self) -> list[SentEmail]:
        return list(self._sent)

    def clear(self) -> None:
        self._sent.clear()
