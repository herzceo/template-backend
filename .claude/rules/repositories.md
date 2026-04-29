---
paths:
  - "backend/domain/repos/**/*.py"
  - "backend/infra/database/psql/repos/**/*.py"
---

# Repository Rules

Repositories follow the ports & adapters pattern: Protocol in `domain/repos/`, implementation in `infra/database/psql/repos/`.

## Protocol Definition (domain/repos/)

```python
from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.domain.entities.user import User
from backend.domain.repos.base import CRUDSupported
from backend.internal import Option

class UserRepo(CRUDSupported[User], Protocol):
    @abstractmethod
    async def get_by_username(self, username: str) -> Option[User]: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Option[User]: ...

    @abstractmethod
    async def assign_role(self, user_id: UUID, role_id: UUID) -> None: ...
```

- Extend `CRUDSupported[Entity]` for standard CRUD operations, or compose from granular protocols (`CreateSupported`, `GetByIdSupported`, etc.)
- All lookup methods MUST return `Option[T]`, not `T | None`
- Custom methods beyond CRUD are `@abstractmethod`

## Implementation (infra/database/psql/repos/)

```python
from typing import final

from backend.domain.entities.user import User
from backend.domain.repos.user import UserRepo
from backend.infra.database.psql.repos.base import ImplCRUDSupported
from backend.internal import Option

@final
class ImplUserRepo(ImplCRUDSupported[User], UserRepo):
    __slots__ = ()

    async def get_by_username(self, username: str) -> Option[User]:
        result = await self._session.execute(
            select(User).where(User.username == username)
        )
        return Option(result.scalar_one_or_none())
```

- Always `@final` on implementation classes
- Inherit from `ImplCRUDSupported[Entity]` AND the Protocol: `ImplXxxRepo(ImplCRUDSupported[Xxx], XxxRepo)`
- `__slots__ = ()` on implementations (session from BaseRepo)

## Gateway Registration

Both the Protocol gateway and implementation gateway must be updated:

```python
# domain/repos/gateway.py -- add property to Protocol
class RepoGateway(Protocol):
    @property
    @abstractmethod
    def user(self) -> UserRepo: ...

# infra/database/psql/repos/gateway.py -- add @cached_property to impl
@final
class ImplRepoGateway(RepoGateway):
    @cached_property
    def user(self) -> ImplUserRepo:
        return ImplUserRepo(self._session)
```
