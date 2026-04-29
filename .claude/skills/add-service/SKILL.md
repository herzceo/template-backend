---
name: add-service
description: Add an application service for complex business logic shared across handlers. Use when logic is too complex for a single handler or is reused.
argument-hint: <domain> <service-name>
---

# Add a Service

Create an application-layer service for complex or reusable business logic.

## Arguments

- `$0` -- Domain name (e.g., `auth`, `billing`, `notifications`)
- `$1` -- Service name (e.g., `identity`, `payment`, `delivery`)

## Current Services

!`find backend/app/rest/v1/services -name "*.py" -not -name "__init__.py" -not -name "__pycache__" 2>/dev/null | sort`

## When to Use a Service

```
Is this logic used by multiple handlers?
├── Yes -> Service
└── No
    Is this logic complex enough to obscure the handler's intent?
    ├── Yes -> Service
    └── No -> Keep it in the handler
```

## Implementation Steps

### 1. Create service

File: `backend/app/rest/v1/services/{name}.py`

```python
from dataclasses import dataclass

from backend.app.errors import AuthenticationRequiredError, ValidationFailedError
from backend.app.shared.ports.auth.password_hasher import PasswordHasher
from backend.domain.enums import IdentityProvider
from backend.domain.repos.database import Database


@dataclass
class {Name}Service:
    db: Database
    password_hasher: PasswordHasher

    async def verify_password(
        self, provider: IdentityProvider, identifier: str, password: str
    ) -> Identity:
        async with self.db:
            identity = (
                await self.db.gateway.identity.get_by_provider_and_identifier(
                    provider, identifier
                )
            ).some(AuthenticationRequiredError(message="Invalid credentials"))

            if not self.password_hasher.verify(password, identity.credential):
                raise AuthenticationRequiredError(message="Invalid credentials")

        return identity
```

### 2. Wire in DI

File: `backend/entry/rest/main/ioc.py`

Add to an appropriate provider:

```python
provider.provide({Name}Service, provides={Name}Service, scope=Scope.REQUEST)
```

### 3. Use in handlers

```python
@dataclass
class LoginHandler(Handler[LoginCommand, AuthContext[dtos.User], None], type_=HandlerType.WRITE):
    db: Database
    {name}_service: {Name}Service

    async def __call__(self, cmd: LoginCommand, _ctx: None = None) -> AuthContext[dtos.User]:
        identity = await self.{name}_service.verify_password(...)
        ...
```

### 4. Verify

Run `just check`.

## Key Rules

- Services are `@dataclass` classes with DI-injected dependencies
- Services live in `backend/app/rest/v1/services/`
- Services depend on ports (Protocols), never on `infra/` implementations
- Services can use the `Database` context manager for transactions
- Services are scoped to `Scope.REQUEST` in the DI container
