---
paths:
  - "backend/entry/rest/main/ioc.py"
  - "backend/entry/queue/ioc.py"
---

# Dependency Injection Rules

DI uses Dishka, an async-first container. All wiring happens in `entry/rest/main/ioc.py` (REST) and `entry/queue/ioc.py` (queue).

## Provider Structure

Group related bindings into provider factory functions:

```python
from dishka import Provider, Scope

def create_database_provider() -> Provider:
    provider = Provider(scope=Scope.REQUEST)
    provider.provide(ImplDatabase, provides=Database)
    return provider
```

## Scopes

- **`Scope.APP`**: singletons -- configs, engine, session maker, HTTP clients
- **`Scope.REQUEST`**: per-request -- `Database`, handlers, services

## Binding Patterns

```python
# Impl -> Protocol
provider.provide(ImplArgon2PasswordHasher, provides=PasswordHasher)

# Config as lambda
provider.provide(lambda: db_config, provides=DatabaseConfig)

# Factory function
provider.provide(create_async_engine, provides=AsyncEngine)

# Handler auto-registration
for handler in handlers.get_defined_rest_handlers().values():
    provider.provide(handler, provides=handler)
```

## Container Composition

```python
def create_container(...) -> AsyncContainer:
    return make_async_container(
        create_utils_provider(db_config),
        create_psql_provider(),
        create_database_provider(),
        create_dbus_provider(),
        create_redis_provider(redis_config, verification_config),
        create_auth_provider(...),
        create_handlers_provider(),
        create_external_provider(...),
    )
```

## Controller Integration

Controllers use `@inject` decorator and `Depends[Type]` for injection:

```python
from backend.internal.di import Depends, inject

@post("/login")
@inject
@result
async def login(self, handler: Depends[LoginHandler]) -> dtos.User:
    ...
```

## Key Rules

- Always bind to the Protocol type: `provides=PasswordHasher`, not `provides=ImplArgon2PasswordHasher`
- Optional external services use conditional wiring: `if config is not None: provider.provide(...)`
- Services go in `Scope.REQUEST`: `provider.provide(IdentityService, provides=IdentityService, scope=Scope.REQUEST)`
- The `GlobalContainer` singleton manages container lifecycle via `backend/internal/di/container.py`

## Config structs, not primitives

Never inject a bare primitive (`int`, `str`, `timedelta`, etc.) through the DI container. The container cannot distinguish two `int` dependencies, and callers can substitute wrong values silently.

Wrap configurable values in a typed `StructDTO` config class and inject that instead:

```python
# wrong — timedelta is ambiguous in the container
@dataclass
class SessionService:
    session_ttl: timedelta

# correct — SessionConfig is unambiguous; the service owns its config shape
class SessionConfig(StructDTO):
    SESSION_TTL_DAYS: int = 14

@dataclass
class SessionService:
    session_config: SessionConfig
```

Place the config struct in the same file as the class that primarily uses it — not in a generic `infra/*/config.py` — so the dependency is obvious and co-located.

Register it as a `Scope.APP` singleton via lambda in the provider that owns it:

```python
provider.provide(lambda: session_config, provides=SessionConfig)
```

Load it from the environment alongside the other configs in `main/cli.py`:

```python
session_config=load_from_env(SessionConfig),
```
