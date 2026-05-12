---
paths:
  - "backend/infra/database/**/*.py"
  - "backend/app/shared/db/**/*.py"
---

# Database Rules

PostgreSQL with SQLAlchemy 2.0 async ORM. Transaction management via `Database` Protocol.

## Database Protocol (app/shared/db/database.py)

```python
class Database(Protocol):
    @property
    def gateway(self) -> RepoGateway: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def flush(self) -> None: ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(...) -> None: ...
```

## Transaction Management

Always wrap DB operations in `async with self.db:`:

```python
async def __call__(self, cmd: CreateUserCommand, _ctx: None = None) -> dtos.User:
    async with self.db:
        user = User(username=cmd.username, email=cmd.email, ...)
        user = (await self.db.gateway.user.create(user)).some(
            AlreadyExistsError(message="User already exists")
        )
        await self.db.commit()
    return dtos.User.from_object(user)
```

- `async with self.db:` opens a session/transaction
- `await self.db.commit()` commits explicitly -- no auto-commit
- Session auto-closes on `__aexit__`
- Supports nested transactions via `begin_nested()`

## Gateway Access

Access repositories only through the gateway, only inside `async with` blocks:

```python
# correct
async with self.db:
    user = (await self.db.gateway.user.get_by_id(user_id)).some(...)

# wrong -- accessing gateway outside context manager
user = await self.db.gateway.user.get_by_id(user_id)
```

## Session Configuration

- `expire_on_commit=False` -- entities remain usable after commit
- `autoflush=False` -- explicit flush/commit only
- Connection pooling via psycopg pool (configurable size/overflow)

## Repository Implementation

```python
@final
class ImplCRUDSupported[E: Base](BaseRepo[E]):
    # _session and _entity auto-resolved from generic arg
    # Provides: create, get_by_id, update, delete_by_id, count, get_for_update, list_with_offset
```

Custom queries use SQLAlchemy `select()`:

```python
async def get_by_username(self, username: str) -> Option[User]:
    result = await self._session.execute(
        select(User).where(User.username == username)
    )
    return Option(result.scalar_one_or_none())
```

## Alembic Migrations

- Migrations in `backend/infra/database/psql/alembic/migrations/versions/`
- Generate: `just migration "add users table"`
- Apply: `just migrate`
- `env.py` imports all entities to register metadata
- Never manually edit existing migration files (protected by guard_paths.py hook)
