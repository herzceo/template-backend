from dataclasses import dataclass, field
from typing import Any


class ApplicationError(Exception):
    """Base type for errors raised by application/use-case code."""


@dataclass(eq=False)
class DetailedError(ApplicationError):
    message: str = ""
    code: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


class NotFoundError(DetailedError):
    message = "Not found"
    code = "not_found"


class InvalidInputError(DetailedError):
    message = "Invalid input"
    code = "invalid_input"


class ValidationFailedError(DetailedError):
    message = "Validation failed"
    code = "validation_failed"


class AlreadyExistsError(DetailedError):
    message = "Already exists"
    code = "already_exists"


class ConflictError(DetailedError):
    message = "Conflict"
    code = "conflict"


class PermissionDeniedError(DetailedError):
    message = "Permission denied"
    code = "permission_denied"


class AuthenticationRequiredError(DetailedError):
    message = "Authentication required"
    code = "authentication_required"
