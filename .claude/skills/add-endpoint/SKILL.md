---
name: add-endpoint
description: Add a complete REST endpoint from command to controller route. Use when building new API endpoints.
argument-hint: <domain> <action> <http-method>
---

# Add a REST Endpoint

Create a full endpoint pipeline: Command -> Handler -> DTO -> Controller route -> DI wiring.

## Arguments

- `$0` -- Domain name (e.g., `users`, `auth`, `roles`)
- `$1` -- Action name (e.g., `create`, `get`, `list`, `update`, `delete`, `login`)
- `$2` -- HTTP method (e.g., `get`, `post`, `patch`, `delete`)

## Current State

Existing handlers:
!`find backend/app/rest/v1/handlers -name "*.py" -not -name "__init__.py" -not -name "__pycache__" -not -path "*/base/*" 2>/dev/null | sort`

Existing controllers:
!`find backend/entry/rest/v1 -maxdepth 1 -name "*.py" -not -name "__init__.py" -not -name "__pycache__" 2>/dev/null | sort`

## Decision Tree

```
Is this a read or write operation?
├── Read (GET, no side effects) -> type_=HandlerType.READ
└── Write (POST/PATCH/DELETE, mutations) -> type_=HandlerType.WRITE

Is this a standard CRUD operation or a custom action?
├── CRUD (create/get/update/delete/list) -> use standard REST paths
└── Custom action (assign, revoke, markRead, signIn, etc.) -> use :camelCaseVerb suffix
    ├── Mutation: @post("/{id:str}:assignRole") with body DTO in entry/rest/v1/dtos.py
    └── Custom read: @get(":listForUser") with query params

Does the handler need path parameters?
├── Yes -> Controller converts str to UUID/enum before creating command
└── No -> Command fields come from request body

Does this return data?
├── Yes -> Define/reuse a response DTO in app/rest/v1/dtos/
└── No -> Handler returns None, controller returns None

Is this a list endpoint?
├── Yes -> Use offset: int = 0, limit: int = 50
└── No -> N/A
```

## Implementation Steps

### 1. Create Command + Handler

File: `backend/app/rest/v1/handlers/{domain}/{action}.py`

```python
from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class Get{Entity}Command(Command):
    {entity}_id: UUID


@dataclass
class Get{Entity}Handler(Handler[Get{Entity}Command, dtos.{Entity}, None], type_=HandlerType.READ):
    db: Database

    async def __call__(self, cmd: Get{Entity}Command, _ctx: None = None) -> dtos.{Entity}:
        async with self.db:
            entity = (await self.db.gateway.{entity}.get_by_id(cmd.{entity}_id)).some(
                NotFoundError(message="{Entity} not found")
            )
        return dtos.{Entity}.from_object(entity)
```

### 2. Export from handler module

File: `backend/app/rest/v1/handlers/{domain}/__init__.py`

Add the new command and handler to `__all__` and imports.

### 3. Create/update response DTO (if needed)

File: `backend/app/rest/v1/dtos/{domain}.py`

```python
from backend.internal.dto import StructDTO

class {Entity}(StructDTO):
    id: str
    # ... fields matching what the entity exposes
    created_at: str
    updated_at: str
```

### 4. Add controller method

File: `backend/entry/rest/v1/{domain}.py`

Standard CRUD:
```python
@{method}("/{entity_id:str}", exclude_from_auth=False)
@inject
@result
async def {action}_{entity}(
    self,
    entity_id: str,
    handler: Depends[{domain}.Get{Entity}Handler],
) -> dtos.{Entity}:
    return await handler({domain}.Get{Entity}Command({entity}_id=UUID(entity_id)))
```

Custom method (non-CRUD action):
```python
@post("/{id:str}:assignRole")
@inject
@result
async def assign_role(
    self,
    id: str,
    data: AssignRoleBody,
    handler: Depends[users.AssignRoleHandler],
) -> None:
    return await handler(users.AssignRoleCommand(user_id=UUID(id), role_id=data.role_id))
```

List endpoint:
```python
@get("/{entities}/")
@inject
@result
async def list_{entities}(
    self,
    handler: Depends[{domain}.List{Entities}Handler],
    offset: int = 0,
    limit: int = 50,
) -> dtos.PaginatedResponse[dtos.{Entity}]:
    return await handler({domain}.List{Entities}Command(offset=offset, limit=limit))
```

### 5. Register controller (if new domain)

File: `backend/entry/rest/v1/__init__.py`

Add to `create_v1_router()` route_handlers list.

### 6. Verify

Run `just check` to ensure type checking and linting pass.
