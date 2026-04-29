---
paths:
  - "backend/entry/rest/v1/**/*.py"
---

# Controller Rules

Controllers are Litestar `Controller` subclasses in `backend/entry/rest/v1/`. They bridge HTTP requests to handlers.

## Controller Structure

```python
from typing import Any

from litestar import Controller, Request, get, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import auth
from backend.entry.rest.common.response import result
from backend.internal.di import Depends, inject


class AuthController(Controller):
    path = "/auth"
    tags = ("Auth",)

    @post("/login", exclude_from_auth=True)
    @inject
    @result
    async def login(
        self,
        data: auth.LoginCommand,
        handler: Depends[auth.LoginHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ctx = await handler(data)
        set_session_token(request.scope, ctx.token)
        return ctx.data
```

## Decorator Order (critical)

The decorator stack MUST be in this exact order (outermost to innermost):

1. `@get(...)` / `@post(...)` / `@patch(...)` / `@delete(...)` -- route definition
2. `@inject` -- enables Dishka DI
3. `@result` -- wraps return in `Ok(data=...)`

## Primitive Conversion

Controllers are the boundary where wire types become domain types. Convert BEFORE creating commands:

```python
@get("/{user_id:str}")
@inject
@result
async def get_user(
    self,
    user_id: UUID,  # Litestar auto-converts path params
    handler: Depends[users.GetUserHandler],
) -> dtos.User:
    return await handler(users.GetUserCommand(user_id=user_id))
```

For enum path params, Litestar handles conversion automatically when typed:

```python
async def initiate_oauth(self, provider: IdentityProvider, ...) -> ...:
    return await handler(auth.InitiateOAuthCommand(provider=provider))
```

## Handler Injection

Handlers are injected via `Depends[HandlerType]`:

```python
handler: Depends[auth.LoginHandler]
```

## Registration

Register controllers in `backend/entry/rest/v1/__init__.py`:

```python
def create_v1_router() -> Router:
    return Router(
        path="/v1",
        route_handlers=[AuthController, UsersController, ...],
    )
```

## Key Rules

- `exclude_from_auth=True` for public endpoints
- One controller per domain (auth, users, roles, etc.)
- Controllers contain NO business logic -- only routing and type conversion
- Command DTOs can be used directly as request body: `data: auth.LoginCommand`
