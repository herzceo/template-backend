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

## Custom Methods

Non-CRUD operations name the action as a trailing `camelCaseVerb` **path segment** (`/verb`), not the Google-style colon (`:verb`).

- **Mutations** use `@post`: `@post("/{id:str}/assignRole")`, `@post("/{id:str}/markRead")`
- **Custom reads** use `@get`: `@get("/listForUser")`
- **Request params** that were previously URL path segments move to a request body DTO: `data: AssignRoleBody`
- Body DTOs for custom methods live in `entry/rest/v1/dtos.py`

**Why slash, not colon.** The Google API Design Guide (AIP-136) puts custom methods after a colon (`/users/{id}:assignRole`) precisely so the verb is not mistaken for a sub-resource. Litestar cannot route that form: `litestar/routes/base.py` splits the path on `/` and `fullmatch`es each segment against `{(.*?)}`, so a path parameter must occupy an entire segment. A mixed segment like `{id:str}:assignRole` fails the `fullmatch`, is stored as a *literal* string, and never matches a real request — the route silently 404s. Only a fully-static segment can carry a colon (`/auth:signIn` would route), but for consistency we use `/verb` everywhere — collection-level (`/auth/signIn`, `/users/listWithRoles`) and resource-level (`/users/{id:str}/assignRole`) alike. This is a deliberate, documented deviation from AIP-136 forced by the framework.

A static verb segment and a sibling `{id}` param segment do not collide: Litestar matches static children before the path-parameter child, so `GET /users/listWithRoles` hits the custom method and `GET /users/{id}` still serves real ids.

Custom methods converted from `@delete` to `@post` MUST use `@result` (returns HTTP 200 with body, not 204).

```python
# Collection-level custom method — path = "" + explicit full path
class AuthController(Controller):
    path = ""
    tags = ("Auth",)

    @post("/auth/signIn", exclude_from_auth=True)
    @inject
    @result
    async def sign_in(self, data: auth.SignInCommand, handler: Depends[auth.SignInHandler]) -> dtos.Session:
        return await handler(data)

# Resource-level custom method — controller path = "/roles"
class RolesController(Controller):
    path = "/roles"
    tags = ("Roles",)

    @post("/{id:str}/assignPermission")
    @inject
    @result
    async def assign_permission(
        self,
        id: str,
        data: AssignPermissionBody,
        handler: Depends[roles.AssignPermissionHandler],
    ) -> None:
        return await handler(roles.AssignPermissionCommand(role_id=UUID(id), permission_id=data.permission_id))
```

## Pagination Parameters

List endpoints use offset-based pagination:

```python
@get("/users/")
@inject
@result
async def list_users(
    self,
    handler: Depends[users.ListUsersHandler],
    offset: int = 0,
    limit: int = 50,
) -> dtos.PaginatedResponse[dtos.User]:
    return await handler(users.ListUsersCommand(offset=offset, limit=limit))
```

## Decorator Order (critical)

The decorator stack MUST be in this exact order (outermost to innermost):

1. `@get(...)` / `@post(...)` / `@patch(...)` / `@delete(...)` -- route definition
2. `@inject` -- enables Dishka DI
3. `@result` -- wraps return in `Ok(data=...)` — **OMIT for `@delete`**

**`@delete` routes must NOT use `@result`**. Litestar sets the default status code to 204 (No Content) for `@delete`, and HTTP 204 must have no response body. The `@result` decorator wraps even `None` returns in `Ok(data=None)`, which has a body and causes a 500 error at runtime.

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
- For controllers with collection-level custom methods, set `path = ""` and use full explicit paths
