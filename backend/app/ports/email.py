from abc import abstractmethod
from enum import StrEnum, auto
from typing import Literal, Protocol, TypedDict


class EmailType(StrEnum):
    EMAIL_VERIFICATION = auto()


class VerificationEmailParams(TypedDict):
    username: str
    code: str


class EmailSender(Protocol):
    @abstractmethod
    async def send(
        self,
        *,
        to: str,
        type: Literal[EmailType.EMAIL_VERIFICATION],
        params: VerificationEmailParams,
    ) -> None: ...
