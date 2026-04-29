---
paths:
  - "backend/**/*.py"
  - "tests/**/*.py"
---

# Code Style Rules

## Formatting

- ruff with `select = ["ALL"]`, line-length 100
- Enforced automatically by `just check` PostToolUse hook

## Runtime

- All Python commands run through `uv run` -- never bare `python3` or `python`
- Shell scripts, justfile recipes, hooks: `uv run python`, `uv run ruff`, `uv run mypy`

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Entity | PascalCase | `User`, `AuditLog` |
| Repository Protocol | `{Entity}Repo` | `UserRepo`, `TenantRepo` |
| Repository Impl | `Impl{Entity}Repo` | `ImplUserRepo` |
| Port Protocol | Capability name | `PasswordHasher`, `OAuthGateway` |
| Adapter | `Impl{Detail}{Port}` | `ImplArgon2PasswordHasher` |
| Handler | `{Action}{Entity}Handler` | `GetUserHandler`, `LoginHandler` |
| Command | `{Action}{Entity}Command` | `GetUserCommand`, `LoginCommand` |
| Service | `{Domain}Service` | `IdentityService`, `SessionService` |
| Event | `{Subject}{Action}` | `UserVerificationRequested` |
| Event Handler | `{EventName}Handler` | `UserVerificationRequestedHandler` |
| File | snake_case | `user.py`, `identity_service.py` |

## File Organization

- One primary class per file
- File named after the primary class (PascalCase -> snake_case)
- `__init__.py` with explicit `__all__` tuple and trailing comma for re-exports

```python
from .login import LoginCommand, LoginHandler
from .signup import SignupCommand, SignupHandler

__all__ = (
    "LoginCommand",
    "LoginHandler",
    "SignupCommand",
    "SignupHandler",
)
```

## Comments

- No useless comments that restate the code
- No section dividers like `# ---- Models ----` or `# -- Config --`
- Only comment where logic is genuinely non-obvious

## Imports

- All imports top-level or inside `if TYPE_CHECKING:`
- Never import inside function bodies
- `from __future__ import annotations` when using TYPE_CHECKING in the same file

## @final

Every concrete class implementing a Protocol gets `@final`:

```python
from typing import final

@final
class ImplUserRepo(ImplCRUDSupported[User], UserRepo):
    ...
```

## Other

- `@dataclass` on handlers, event handlers, services (not `__init__`)
- `__slots__ = ()` on repo implementations
- Prefer `|` union syntax over `Union[]`: `str | None` not `Optional[str]`
