---
paths:
  - "backend/domain/entities/**/*.py"
---

# Entity Rules

Entities are SQLAlchemy ORM models in `backend/domain/entities/`.

## Mixin Inheritance Order

Always use this exact MRO: `WithUUIDID, WithActive, WithTime, WithTenant, Base`

Only include mixins that apply. `Base` is always last. Omit mixins that don't belong to the entity:
- Omit `WithActive` for entities that are never independently deactivated (e.g., `Profile` — it lives and dies with `User`)
- Omit `WithTenant` for entities that inherit tenancy indirectly via an FK to `User` or `Tenant`

```python
from .base import Base, WithActive, WithTenant, WithTime, WithUUIDID

# Full set — identity entity with lifecycle and tenancy
class User(WithUUIDID, WithActive, WithTime, WithTenant, Base):
    ...

# Companion entity — tied 1:1 to User; inherits tenancy through user_id FK
class Profile(WithUUIDID, WithTime, Base):
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

## Companion Entities

A companion entity is a 1:1 satellite of a primary entity that carries a distinct concern. The canonical example is `Profile` — it holds presentation data (`display_name`, `avatar_url`) separated from identity data (`User`).

Rules for companion entities:
- Use `WithUUIDID, WithTime, Base` (no `WithActive`, no `WithTenant`)
- Add a `UNIQUE` FK to the primary entity with `ondelete="CASCADE"`
- Always create the companion in the **same transaction** as the primary entity — never create it lazily
- Give it a dedicated repo with `get_by_primary_id` instead of `get_by_id`
- Give it dedicated endpoints (`GET /primary/{id}/companion`, `PATCH /primary/{id}/companion`)

```python
class Profile(WithUUIDID, WithTime, Base):
    user_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user: Mapped[User] = relationship(backref="profile", lazy="raise")
```
