---
paths:
  - "backend/app/shared/events/**/*.py"
  - "backend/app/events/**/*.py"
  - "backend/infra/dbus/**/*.py"
---

# Event Rules

Events enable async background processing via a PostgreSQL-backed job queue.

## Event Definition (app/shared/events/v1/)

```python
from typing import ClassVar
from uuid import UUID

from backend.app.shared.events.base import BaseEvent

class UserVerificationRequested(BaseEvent):
    name: ClassVar[str] = "user_verification_requested"
    user_id: UUID
    email: str
    username: str
```

- Extend `BaseEvent(StructDTO, kw_only=True)` which provides `id` and `created_at`
- `name: ClassVar[str]` must be unique, snake_case -- this is the key for handler dispatch
- Data fields are the event payload

## Publishing (in handlers)

```python
from backend.app.shared.db.dbus import DBus

@dataclass
class SignupHandler(Handler[...]):
    dbus: DBus

    async def __call__(self, cmd, _ctx=None):
        async with self.db:
            ...
            await self.dbus.publish(
                UserVerificationRequested(
                    user_id=user.id, email=user.email, username=user.username
                )
            )
```

- Inject `dbus: DBus` as a handler dependency
- Publish inside the `async with self.db:` block (event becomes a job in the same transaction)
- `DBus.publish()` returns a job ID
- Options: `priority`, `execution_lock`, `queueing_lock`, `scheduled_at`

## Event Handler (app/events/v1/handlers/)

```python
from dataclasses import dataclass

from backend.app.events.v1.handlers.base import EventHandler
from backend.app.shared.events.v1.user_verification_requested import UserVerificationRequested

@dataclass
class UserVerificationRequestedHandler(EventHandler[UserVerificationRequested]):
    email_sender: EmailSender
    verification_store: VerificationCodeStore

    async def __call__(self, event: UserVerificationRequested, /) -> None:
        raw_code = await self.verification_store.issue_code(event.user_id)
        await self.email_sender.send(
            to=event.email,
            type=EmailType.EMAIL_VERIFICATION,
            params={"username": event.username, "code": raw_code},
        )
```

- Extend `EventHandler[EventType]` -- auto-registers keyed by `event_type.name`
- `@dataclass` with DI-injected dependencies
- `__call__` receives the deserialized event
- Returns `None` always

## Registration

Import handler modules in `backend/app/events/v1/handlers/__init__.py` to trigger auto-registration:

```python
from . import auth
```

## Queue Execution

The queue executor (`entry/queue/`) polls for jobs, deserializes events from job args, resolves handlers from DI, and calls them with request-scoped containers.
