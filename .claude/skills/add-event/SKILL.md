---
name: add-event
description: Add a new domain event with its publisher call and background event handler. Use for async side effects.
argument-hint: <event-name>
---

# Add an Event

Create a domain event, publish it from a handler, and create a background event handler.

## Arguments

- `$0` -- Event name in PascalCase (e.g., `InvoiceSent`, `UserDeactivated`, `OrderCompleted`)

## Current Events

Definitions:
!`find backend/app/shared/events -name "*.py" -not -name "__init__.py" -not -name "__pycache__" -not -name "base.py" 2>/dev/null | sort`

Handlers:
!`find backend/app/events -name "*.py" -not -name "__init__.py" -not -name "__pycache__" -not -path "*/base/*" 2>/dev/null | sort`

## Implementation Steps

### 1. Create event definition

File: `backend/app/shared/events/v1/{name}.py`

```python
from typing import ClassVar
from uuid import UUID

from backend.app.shared.events.base import BaseEvent


class {EventName}(BaseEvent):
    name: ClassVar[str] = "{event_name_snake_case}"
    # payload fields
    user_id: UUID
    reason: str
```

### 2. Export from events module

File: `backend/app/shared/events/v1/__init__.py`

Add to imports and `__all__`.

### 3. Publish from originating handler

In the handler that triggers the event, inject `dbus: DBus` and publish:

```python
from backend.app.shared.ports.events.dbus import DBus
from backend.app.shared.events.v1.{name} import {EventName}

@dataclass
class SomeHandler(Handler[...]):
    db: Database
    dbus: DBus

    async def __call__(self, cmd, _ctx=None):
        async with self.db:
            # ... business logic ...
            await self.dbus.publish(
                {EventName}(user_id=user.id, reason="...")
            )
            await self.db.commit()
```

### 4. Create event handler

File: `backend/app/events/v1/handlers/{domain}/{name}.py`

```python
from dataclasses import dataclass

from backend.app.events.v1.handlers.base import EventHandler
from backend.app.shared.events.v1.{name} import {EventName}


@dataclass
class {EventName}Handler(EventHandler[{EventName}]):
    # inject dependencies for the side effect
    email_sender: EmailSender

    async def __call__(self, event: {EventName}, /) -> None:
        # handle the event (send email, update analytics, etc.)
        await self.email_sender.send(
            to=event.email,
            type=EmailType.NOTIFICATION,
            params={"reason": event.reason},
        )
```

### 5. Register handler module

File: `backend/app/events/v1/handlers/__init__.py`

Import the handler's domain module:

```python
from . import auth, {domain}
```

If this is a new domain, create `backend/app/events/v1/handlers/{domain}/__init__.py` with the handler import.

### 6. Wire event handler dependencies (if needed)

If the event handler has dependencies not already in the queue's DI container, add them to `backend/entry/queue/ioc.py`.

### 7. Verify

Run `just check`.
