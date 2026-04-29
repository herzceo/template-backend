---
name: add-entity
description: Add a new domain entity with SQLAlchemy mixins and generate an Alembic migration. Use when defining new database tables.
argument-hint: <entity-name> <fields-comma-separated>
---

# Add a Domain Entity

Create a new SQLAlchemy ORM model with appropriate mixins and generate a migration.

## Arguments

- `$0` -- Entity name in PascalCase (e.g., `Invoice`, `Subscription`)
- `$1` -- Comma-separated fields (e.g., `amount:int,currency:str,status:str,due_at:datetime`)

## Current Entities

!`find backend/domain/entities -name "*.py" -not -name "__init__.py" -not -name "__pycache__" -not -path "*/base/*" 2>/dev/null | sort`

## Implementation Steps

### 1. Create entity file

File: `backend/domain/entities/{name}.py`

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, WithActive, WithTenant, WithTime, WithUUIDID

if TYPE_CHECKING:
    pass  # relationship type imports here


class {Name}(WithUUIDID, WithActive, WithTime, WithTenant, Base):
    # columns here
    title: Mapped[str] = mapped_column(String(255), nullable=False)
```

### Mixin selection

```
Does it need a UUID primary key? -> WithUUIDID (almost always yes)
Does it need is_active flag?     -> WithActive
Does it need created_at/updated_at? -> WithTime
Does it belong to a tenant?      -> WithTenant
```

Mixin order: `WithUUIDID, WithActive, WithTime, WithTenant, Base`

### Column type reference

| Python Type | SQLAlchemy | Notes |
|-------------|-----------|-------|
| `str` | `String` or `String(N)` | Use `String(N)` for bounded length |
| `int` | `Integer` | |
| `float` | `Float` | |
| `bool` | `Boolean` | |
| `datetime` | `DateTime(timezone=True)` | Always use timezone=True |
| `UUID` | `Uuid` (from sqlalchemy) | For foreign keys |
| `str \| None` | `String, nullable=True` | Mapped[str \| None] |

### Relationships

```python
if TYPE_CHECKING:
    from .user import User

class Invoice(WithUUIDID, WithActive, WithTime, WithTenant, Base):
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    user: Mapped[User] = relationship(lazy="raise")
```

### 2. Export from entities module

File: `backend/domain/entities/__init__.py`

Add import of the new entity so Alembic picks it up.

### 3. Generate migration

```bash
just migration "add {name} table"
```

### 4. Review migration

Read the generated file in `backend/infra/database/alembic/migrations/versions/`. Check for correct column types, indexes, and constraints.

### 5. Apply migration

```bash
just migrate
```

### 6. Verify

Run `just check`.
