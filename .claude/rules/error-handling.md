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

Exception handlers in `entry/rest/main/exc/` map `ApplicationError` subclasses to HTTP responses with `ErrorDetail(code, message, details)`. The response wrapper returns `Err(error=ErrorDetail(...))`.

## Key Rules

- Handlers raise domain errors directly -- framework maps them to HTTP status codes
- Never catch generic `Exception` in handlers
- Never raise `ValueError` or `TypeError` for business logic -- use the error hierarchy
- Always pass a descriptive `message` when raising errors
