from abc import abstractmethod
from enum import StrEnum, auto
from typing import Protocol, TypedDict


class EmailType(StrEnum):
    EMAIL_VERIFICATION = auto()
    LOGIN_CODE = auto()
    PASSWORD_RESET = auto()
    EMAIL_CHANGE_VERIFICATION = auto()
    SIGN_IN_METHOD_ADDED = auto()


class VerificationEmailParams(TypedDict):
    username: str
    code: str


class LoginCodeParams(TypedDict):
    username: str
    code: str


class PasswordResetParams(TypedDict):
    username: str
    reset_url: str


class EmailChangeParams(TypedDict):
    username: str
    confirm_url: str


class SignInMethodAddedParams(TypedDict):
    username: str
    provider: str


type EmailParams = (
    VerificationEmailParams
    | LoginCodeParams
    | PasswordResetParams
    | EmailChangeParams
    | SignInMethodAddedParams
)


class EmailSender(Protocol):
    @abstractmethod
    async def send(
        self,
        *,
        to: str,
        type: EmailType,
        params: EmailParams,
    ) -> None: ...
