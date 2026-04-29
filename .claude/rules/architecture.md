---
paths:
  - "backend/**/*.py"
---

# Architecture Rules

This project follows hexagonal (ports & adapters) architecture with strict layer boundaries.

## Layers and Responsibilities

| Layer | Path | Responsibility |
|-------|------|---------------|
| `domain/` | `backend/domain/` | Entities (ORM models), repository Protocol interfaces, enums |
| `app/` | `backend/app/` | Use cases (handlers), services, shared ports (Protocols), DTOs, errors, events |
| `entry/` | `backend/entry/` | Framework glue: controllers, middleware, DI wiring, app factory, exception mapping |
| `infra/` | `backend/infra/` | Concrete implementations: database repos, Redis, HTTP clients, S3, security |
| `internal/` | `backend/internal/` | Utilities shared across all layers: Result, Option, StructDTO, DI helpers |
| `main/` | `backend/main/` | CLI bootstrap, composition root |

## Import Direction (enforced by guard_layers.py hook)

```
domain/   -> domain/, internal/
app/      -> app/, domain/, internal/
entry/    -> anything in backend.*
infra/    -> infra/, domain/, backend.app.shared.* (ports only), internal/
internal/ -> internal/
main/     -> anything in backend.*
```

## Forbidden Patterns

```python
# app/ importing from infra/ -- VIOLATION
from backend.infra.database.psql.repos import ImplUserRepo      # wrong
from backend.infra.security.password_hasher import ImplArgon2PasswordHasher  # wrong

# app/ must use Protocol ports instead
from backend.domain.repos.database import Database               # correct
from backend.app.shared.ports.auth.password_hasher import PasswordHasher     # correct
```

```python
# infra/ importing non-shared app code -- VIOLATION
from backend.app.rest.v1.handlers.auth.login import LoginHandler  # wrong
from backend.app.rest.v1.services.identity import IdentityService # wrong

# infra/ may only import from app.shared (ports, events)
from backend.app.shared.ports.auth.password_hasher import PasswordHasher  # correct
from backend.app.shared.events.v1.user_verification_requested import UserVerificationRequested  # correct
```

```python
# domain/ importing from app/ -- VIOLATION
from backend.app.errors import NotFoundError  # wrong

# domain/ only imports from domain/ and internal/
from backend.domain.entities.base import Base  # correct
from backend.internal import Option            # correct
```

## Dependency Inversion

The `app/` layer defines abstract interfaces (Protocols) in `app/shared/ports/`. The `infra/` layer implements them. They are wired together only in `entry/` (the DI container in `entry/rest/main/ioc.py`).

```
app/shared/ports/auth/password_hasher.py  -> Protocol definition
infra/security/password_hasher.py          -> @final implementation
entry/rest/main/ioc.py                     -> provider.provide(ImplArgon2PasswordHasher, provides=PasswordHasher)
```
