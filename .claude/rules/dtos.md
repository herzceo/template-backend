---
paths:
  - "backend/app/rest/v1/dtos/**/*.py"
  - "backend/entry/rest/v1/dtos.py"
---

# DTO Rules

All DTOs inherit from `StructDTO` (msgspec.Struct). Never use Pydantic.

## Two DTO Layers

| Layer | Path | Purpose |
|-------|------|---------|
| App DTOs | `backend/app/rest/v1/dtos/` | Response shapes sent to clients |
| Entry DTOs | `backend/entry/rest/v1/dtos.py` | Request body shapes received from clients |

## App DTOs (Response)

```python
from backend.internal.dto import StructDTO

class User(StructDTO):
    id: str
    username: str
    email: str | None
    first_name: str
    last_name: str
    avatar_url: str | None
    is_verified: bool
    is_active: bool
    created_at: str
    updated_at: str
```

- Use `str` for UUID and datetime fields (msgspec auto-serializes)
- Convert from entity: `User.from_object(user_entity)` -- maps attributes by name
- One file per domain: `dtos/user.py`, `dtos/auth.py`, etc.

## Entry DTOs (Request Body)

```python
from backend.internal.dto import StructDTO

class UpdateUserBody(StructDTO, kw_only=True):
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
```

- Used in controllers as request body type: `data: UpdateUserBody`
- Optional fields use `| None = None` for partial updates
- Spread into commands: `**msgspec.structs.asdict(data)`

## Generic Wrappers

```python
class AuthContext[T](StructDTO):
    token: str
    data: T
```

## Key Rules

- Never return raw entities from handlers -- always convert to DTOs
- `from_object(entity)` handles the ORM-to-DTO mapping
- `to_builtins()` converts DTO to dict for JSON serialization
- `from_builtins(data)` constructs DTO from dict
