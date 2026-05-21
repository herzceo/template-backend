from typing import Any, ClassVar


class ApplicationError(Exception):
    """Base type for errors raised by application/use-case code."""


class DetailedError(ApplicationError):
    _default_message: ClassVar[str] = ""
    _default_code: ClassVar[str] = ""

    def __init__(
        self,
        *,
        message: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message if message is not None else self._default_message
        self.code = code if code is not None else self._default_code
        self.details = details if details is not None else {}
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class NotFoundError(DetailedError):
    _default_message = "Not found"
    _default_code = "not_found"


class InvalidInputError(DetailedError):
    _default_message = "Invalid input"
    _default_code = "invalid_input"


class ValidationFailedError(DetailedError):
    _default_message = "Validation failed"
    _default_code = "validation_failed"


class AlreadyExistsError(DetailedError):
    _default_message = "Already exists"
    _default_code = "already_exists"


class ConflictError(DetailedError):
    _default_message = "Conflict"
    _default_code = "conflict"


class PermissionDeniedError(DetailedError):
    _default_message = "Permission denied"
    _default_code = "permission_denied"


class AuthenticationRequiredError(DetailedError):
    _default_message = "Authentication required"
    _default_code = "authentication_required"
