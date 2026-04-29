---
paths:
  - "backend/**/*.py"
---

# Typing Rules

Strict mypy is enforced with `disallow_untyped_defs`, `disallow_any_unimported`, `disallow_any_generics`.

## Python 3.12+ Generics

Use the new syntax, not `Generic[T]`:

```python
# correct
class Handler[C: Command, R: StructDTO | None, X: StructDTO | None](ABC):
    ...

class Option[T]:
    value: T | None

type Result[T, E] = Ok[T] | Err[E]

# wrong
from typing import Generic, TypeVar
T = TypeVar("T")
class Option(Generic[T]):
    ...
```

## TYPE_CHECKING Imports

Use `TYPE_CHECKING` blocks for type-only imports that would cause circular dependencies or are not needed at runtime:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.infra.external.http.discord.config import DiscordOAuthConfig
```

`from __future__ import annotations` is required when using TYPE_CHECKING imports in the same file for forward references.

## All Imports Top-Level

Never import inside function bodies. All imports go at the top of the file or inside `if TYPE_CHECKING:`.

```python
# wrong
def create_engine():
    from sqlalchemy import create_engine
    ...

# correct
from sqlalchemy import create_engine
```

## Type Annotations

- All function parameters and returns typed
- No `Any` except where genuinely unavoidable (e.g., Litestar `Request[Any, Any, Any]`)
- `ClassVar[type[X]]` for class-level type annotations
- `Mapped[T]` for all entity columns
- `Protocol` for all interfaces/ports

## @overload

Use `@overload` to express return-type variations based on input types. Keeps call sites fully typed without casts.

```python
from typing import overload

@overload
async def get_by_id(self, id_: UUID, /, *, strict: Literal[True]) -> User: ...
@overload
async def get_by_id(self, id_: UUID, /, *, strict: Literal[False] = ...) -> Option[User]: ...

async def get_by_id(self, id_: UUID, /, *, strict: bool = False) -> User | Option[User]:
    result = Option(await self._fetch(id_))
    if strict:
        return result.some(NotFoundError())
    return result
```

Common uses:
- Methods that return `T` or `Option[T]` depending on a flag
- Factory functions that return different types based on a discriminator
- Serialization helpers where the return type depends on the input type

## @final Decorator

Use `@final` (from `typing`) on every concrete class that implements a Protocol:

```python
from typing import final

@final
class ImplArgon2PasswordHasher(PasswordHasher):
    ...
```
