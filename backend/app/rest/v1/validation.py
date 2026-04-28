import re

from email_validator import EmailNotValidError, validate_email

from backend.app.errors import InvalidInputError

_USERNAME_RE = re.compile(r"^[a-z0-9_]+$")
_USERNAME_MIN = 3
_USERNAME_MAX = 32


def sanitize_username_chars(raw: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in raw.lower())


def normalize_username(raw: str) -> str:
    username = sanitize_username_chars(raw)
    if len(username) < _USERNAME_MIN or len(username) > _USERNAME_MAX:
        raise InvalidInputError(
            message=f"Username must be between {_USERNAME_MIN} and {_USERNAME_MAX} characters",
        )
    if not _USERNAME_RE.fullmatch(username):
        raise InvalidInputError(
            message="Username may only contain lowercase letters, digits, and underscores",
        )
    return username


def normalize_email(raw: str) -> str:
    try:
        info = validate_email(raw, check_deliverability=False)
    except EmailNotValidError as exc:
        raise InvalidInputError(message=str(exc)) from exc
    return info.normalized
