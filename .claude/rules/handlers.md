---
paths:
  - "backend/app/rest/v1/handlers/**/*.py"
---

# Handler Rules

Handlers are the use-case layer for REST endpoints, living in `backend/app/rest/v1/handlers/`.

## Structure

One handler per file. File named after the action: `create.py`, `get.py`, `list.py`, `update.py`, `delete.py`, `login.py`, etc.

## Command

Every handler has a Command -- the typed input. Commands extend `Command` (which extends `StructDTO`).

```python
from backend.app.rest.v1.handlers.base import Command

class LoginCommand(Command):
    username: str
    password: str
```

Commands contain fully-typed fields. Never `str` for UUIDs or enums -- the controller converts primitives before creating the command.

## Handler Class

```python
from dataclasses import dataclass

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database

class GetUserCommand(Command):
    user_id: UUID

@dataclass
class GetUserHandler(Handler[GetUserCommand, dtos.User, None], type_=HandlerType.READ):
    db: Database

    async def __call__(self, cmd: GetUserCommand, _ctx: None = None) -> dtos.User:
        async with self.db:
            user = (await self.db.gateway.user.get_by_id(cmd.user_id)).some(
                NotFoundError(message="User not found")
            )
        return dtos.User.from_object(user)
```

## Key Rules

- **Generic parameters**: `Handler[CommandType, ResponseDTO, ContextType]`. Context is usually `None`.
- **`type_=HandlerType.READ`** for queries, **`type_=HandlerType.WRITE`** for mutations.
- **Dependencies**: injected as `@dataclass` fields (not constructor args).
- **Transaction scope**: always wrap DB work in `async with self.db:`.
- **Return DTOs outside the block**: call `DTO.from_object(entity)` AFTER `async with self.db:` closes. `ImplDatabase.__aexit__` expunges all objects before calling rollback, so scalar attributes remain accessible on detached entities. Never access relationship attributes (all `lazy="raise"`) outside the block — DTOs must not map relationships.
- **Option unwrap**: use `.some(ErrorInstance)` on repo lookups, never manual `if x is None`.
- **Auto-registration**: handlers register themselves via `__init_subclass__`. No manual wiring needed.

## Exports

Export command and handler from the domain's `__init__.py`:

```python
# backend/app/rest/v1/handlers/auth/__init__.py
from .login import LoginCommand, LoginHandler

__all__ = ("LoginCommand", "LoginHandler")
```
