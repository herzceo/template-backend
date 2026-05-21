---
paths:
  - "backend/app/errors.py"
  - "backend/entry/rest/main/exc/**/*.py"
  - "backend/app/rest/v1/handlers/**/*.py"
---

# Error Handling Rules

## Error Hierarchy (app/errors.py)

```python
ApplicationError                         # Base
  DetailedError(message, code, details)  # Structured
    NotFoundError                        # 404
    InvalidInputError                    # 400
    ValidationFailedError                # 422
    AlreadyExistsError                   # 409
    ConflictError                        # 409
    PermissionDeniedError                # 403
    AuthenticationRequiredError          # 401
```

## Subclass defaults — never use `@dataclass` on `DetailedError`

`DetailedError` is **not** a dataclass. It uses `_default_message` / `_default_code` as `ClassVar[str]` and a manual `__init__` that falls back to those class-level defaults when the caller does not pass `message=` / `code=`.

Do not "simplify" this back to `@dataclass(eq=False)` with `code: str = ""` as a field. If you do, every subclass override (`code = "not_found"`) is silently shadowed by the dataclass-generated `__init__`, which writes the empty default to every instance. The exception will look correct at the class level (`NotFoundError.code == "not_found"`) but `instance.code` will be `""` — and the gRPC mapper will fall back to `INTERNAL` for every error.

When adding a new error type, override the `ClassVar`s only:

```python
class TooManyAttemptsError(DetailedError):
    _default_message = "Too many attempts"
    _default_code = "too_many_attempts"
```

Never add `code: str = ...` as a class-level annotation in a subclass — that turns it back into a (shadowed) attribute.

Raise with custom message: `raise NotFoundError(message="User not found")`

Raise with details: `raise ValidationFailedError(message="Invalid email", details={"field": "email"})`

## Option.some() Pattern

All repository lookups return `Option[T]`. Unwrap with `.some(exception)`:

```python
# correct
user = (await self.db.gateway.user.get_by_id(user_id)).some(
    NotFoundError(message="User not found")
)

# wrong -- manual None check
result = await self.db.gateway.user.get_by_id(user_id)
if result.value is None:
    raise NotFoundError(message="User not found")
user = result.value
```

Other Option methods:
- `.none(exc)` -- raise if value IS present (for uniqueness checks)
- `.some_or(default)` -- return value or default without raising

## Result Pattern

HTTP client responses use `Result[T, E] = Ok[T] | Err[E]`:

```python
result = await self.client.get_user(user_id)
user = result.raise_()  # returns T if Ok, raises if Err
```

## Exception Mapping (entry/rest/main/exc/)

Exception handlers in `entry/rest/main/exc/` map `ApplicationError` subclasses to HTTP responses following the `google.rpc.Status` shape:

```python
class ErrorDetail(StructDTO):
    code: int        # HTTP status code as integer (e.g. 404)
    message: str     # human-readable message
    status: str      # gRPC status name (e.g. "NOT_FOUND", "INVALID_ARGUMENT")
    details: list[dict[str, Any]]  # list of google.rpc typed error details
```

The response wrapper returns `Err(error=ErrorDetail(...))`. Domain error `code` strings (e.g., `"not_found"`) appear inside `details` as an `ErrorInfo` entry:

```json
{
  "error": {
    "code": 404,
    "message": "User not found",
    "status": "NOT_FOUND",
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
        "reason": "NOT_FOUND",
        "domain": "api",
        "metadata": {}
      }
    ]
  }
}
```

The mapping from domain error codes to gRPC status names lives in `ERROR_CODE_TO_GRPC_STATUS` in `entry/rest/main/exc/handler.py`.

## Key Rules

- Handlers raise domain errors directly -- framework maps them to HTTP status codes
- Never catch generic `Exception` in handlers
- Never raise `ValueError` or `TypeError` for business logic -- use the error hierarchy
- Always pass a descriptive `message` when raising errors
