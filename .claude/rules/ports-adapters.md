---
paths:
  - "backend/app/shared/ports/**/*.py"
  - "backend/infra/external/adapters/**/*.py"
---

# Port & Adapter Rules

Ports are abstract interfaces. Adapters are concrete implementations. They enforce dependency inversion between `app/` and `infra/`.

## Port (Protocol)

Ports live in `backend/app/shared/ports/{category}/`. Categories: `auth/`, `events/`, `outreach/`, `security/`, `storage/`.

```python
# backend/app/shared/ports/auth/password_hasher.py
from typing import Protocol

class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, hash_: str) -> bool: ...
```

- Always `Protocol`, never `ABC`
- Methods are abstract by convention (Protocol methods are implicitly abstract)
- Named after the capability, not the implementation: `PasswordHasher`, not `Argon2Hasher`

## Adapter (Implementation)

Adapters live in `backend/infra/external/adapters/` or `backend/infra/security/`. NOT next to HTTP clients.

```python
# backend/infra/security/password_hasher.py
from typing import final

from argon2 import PasswordHasher as Argon2Hasher

from backend.app.shared.ports.auth.password_hasher import PasswordHasher

@final
class ImplArgon2PasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self._hasher = Argon2Hasher()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, hash_: str) -> bool:
        return self._hasher.verify(hash_, password)
```

- Always `@final`
- Naming: `Impl{Detail}{PortName}` -- e.g., `ImplArgon2PasswordHasher`, `ImplHMACOAuthStateSigner`
- Receives infrastructure dependencies (HTTP clients, configs) via constructor

## Adapter Placement

```
app/shared/ports/auth/oauth_gateway.py     Port Protocol
infra/external/adapters/oauth/gateway.py   Adapter (implements port)
infra/external/http/google_oauth/          HTTP client (transport only)
```

HTTP clients in `infra/external/http/` handle raw HTTP. Adapters in `infra/external/adapters/` translate between port interface and client.

## DI Wiring

Ports and adapters are wired in `entry/rest/main/ioc.py`:

```python
provider.provide(ImplArgon2PasswordHasher, provides=PasswordHasher)
```

Handlers depend on the port type, never the adapter:

```python
@dataclass
class SignupHandler(Handler[...]):
    password_hasher: PasswordHasher  # Port, not ImplArgon2PasswordHasher
```
