from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from backend.app.shared.ports.outreach.email import EmailParams, EmailType


@dataclass
class SentEmail:
    to: str
    type: EmailType
    # Widened to a plain mapping so tests can index any key regardless of which
    # EmailParams variant was sent.
    params: Mapping[str, object]


@final
@dataclass
class MockEmailSender:
    _sent: list[SentEmail] = field(default_factory=list)

    async def send(
        self,
        *,
        to: str,
        type: EmailType,
        params: EmailParams,
    ) -> None:
        self._sent.append(SentEmail(to=to, type=type, params=params))

    def get_sent(self) -> list[SentEmail]:
        return list(self._sent)

    def clear(self) -> None:
        self._sent.clear()
