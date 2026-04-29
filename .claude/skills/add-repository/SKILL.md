---
name: add-repository
description: Add a new repository protocol and implementation with gateway registration. Use after creating a new entity.
argument-hint: <entity-name>
---

# Add a Repository

Create a repository Protocol (port) and its PostgreSQL implementation (adapter), then wire into the gateway.

## Arguments

- `$0` -- Entity name in PascalCase (e.g., `Invoice`)

## Current Repositories

Protocol interfaces:
!`find backend/domain/repos -name "*.py" -not -name "__init__.py" -not -name "__pycache__" -not -name "base.py" -not -name "gateway.py" -not -name "database.py" 2>/dev/null | sort`

Implementations:
!`find backend/infra/database/psql/repos -name "*.py" -not -name "__init__.py" -not -name "__pycache__" -not -name "base.py" -not -name "gateway.py" -not -name "database.py" 2>/dev/null | sort`

## Implementation Steps

### 1. Create Protocol

File: `backend/domain/repos/{name}.py`

```python
from abc import abstractmethod
from typing import Protocol

from backend.domain.entities.{name} import {Name}
from backend.domain.repos.base import CRUDSupported
from backend.internal import Option


class {Name}Repo(CRUDSupported[{Name}], Protocol):
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Option[{Name}]: ...
```

### 2. Add to Protocol gateway

File: `backend/domain/repos/gateway.py`

```python
from .{name} import {Name}Repo

class RepoGateway(Protocol):
    # ... existing properties ...

    @property
    @abstractmethod
    def {name}(self) -> {Name}Repo: ...
```

### 3. Create Implementation

File: `backend/infra/database/psql/repos/{name}.py`

```python
from typing import final

from sqlalchemy import select

from backend.domain.entities.{name} import {Name}
from backend.domain.repos.{name} import {Name}Repo
from backend.infra.database.psql.repos.base import ImplCRUDSupported
from backend.internal import Option


@final
class Impl{Name}Repo(ImplCRUDSupported[{Name}], {Name}Repo):
    __slots__ = ()

    async def get_by_slug(self, slug: str) -> Option[{Name}]:
        result = await self._session.execute(
            select({Name}).where({Name}.slug == slug)
        )
        return Option(result.scalar_one_or_none())
```

### 4. Add to Implementation gateway

File: `backend/infra/database/psql/repos/gateway.py`

```python
from .{name} import Impl{Name}Repo

@final
class ImplRepoGateway(RepoGateway):
    # ... existing properties ...

    @cached_property
    def {name}(self) -> Impl{Name}Repo:
        return Impl{Name}Repo(self._session)
```

### 5. Export from modules

Add to `backend/domain/repos/__init__.py` and `backend/infra/database/psql/repos/__init__.py`.

### 6. Verify

Run `just check`.
