---
paths:
  - "backend/domain/entities/**/*.py"
---

# Entity Rules

Entities are SQLAlchemy ORM models in `backend/domain/entities/`.

## Mixin Inheritance Order

Always use this exact MRO: `WithUUIDID, WithActive, WithTime, WithTenant, Base`

Only include mixins that apply. `Base` is always last.

```python
from .base import Base, WithActive, WithTenant, WithTime, WithUUIDID

class User(WithUUIDID, WithActive, WithTime, WithTenant, Base):
    ...
```

## Column Definitions

Always use `Mapped[T]` with `mapped_column()`. Never use raw `Column()`.

```python
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

class User(WithUUIDID, WithActive, WithTime, WithTenant, Base):
    username: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

## Relationships

Use `lazy="raise"` to prevent N+1 queries. Guard relationship type imports with `TYPE_CHECKING`.

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, relationship

if TYPE_CHECKING:
    from .role import Role

class User(WithUUIDID, WithActive, WithTime, WithTenant, Base):
    roles: Mapped[list[Role]] = relationship(secondary=user_role, backref="users", lazy="raise")
```

## Table Naming

Tables are auto-named by converting the class name from PascalCase to snake_case. Do NOT set `__tablename__` explicitly.

## Registration

Export every new entity from `backend/domain/entities/__init__.py`. Alembic's `env.py` imports that module to discover all models for migration autogeneration.

## Properties

Computed properties that derive from columns are fine:

```python
@property
def is_verified(self) -> bool:
    return self.verified_at is not None
```
