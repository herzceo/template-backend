---
name: add-handler
description: Add a new command and handler for a use case. Use when adding business logic for an existing entity.
argument-hint: <domain> <action>
---

# Add a Handler

Create a Command + Handler pair for a use case.

## Arguments

- `$0` -- Domain name (e.g., `users`, `auth`, `invoices`)
- `$1` -- Action name (e.g., `create`, `archive`, `send`, `verify`)

## Current Handlers

!`find backend/app/rest/v1/handlers -name "*.py" -not -name "__init__.py" -not -name "__pycache__" -not -path "*/base/*" 2>/dev/null | sort`

## Implementation Steps

### 1. Create handler file

File: `backend/app/rest/v1/handlers/{domain}/{action}.py`

```python
from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class {Action}{Entity}Command(Command):
    {entity}_id: UUID


@dataclass
class {Action}{Entity}Handler(
    Handler[{Action}{Entity}Command, dtos.{Entity}, None],
    type_=HandlerType.WRITE,
):
    db: Database

    async def __call__(
        self, cmd: {Action}{Entity}Command, _ctx: None = None
    ) -> dtos.{Entity}:
        async with self.db:
            entity = (await self.db.gateway.{entity}.get_by_id(cmd.{entity}_id)).some(
                NotFoundError(message="{Entity} not found")
            )
            # ... business logic ...
            entity = (await self.db.gateway.{entity}.update(entity)).some(
                NotFoundError(message="{Entity} not found")
            )
            await self.db.commit()
        return dtos.{Entity}.from_object(entity)
```

### Handler with additional dependencies

```python
@dataclass
class SendInvoiceHandler(
    Handler[SendInvoiceCommand, None, None],
    type_=HandlerType.WRITE,
):
    db: Database
    dbus: DBus
    email_sender: EmailSender  # Port, not implementation

    async def __call__(self, cmd: SendInvoiceCommand, _ctx: None = None) -> None:
        async with self.db:
            invoice = (await self.db.gateway.invoice.get_by_id(cmd.invoice_id)).some(
                NotFoundError(message="Invoice not found")
            )
            # business logic
            await self.dbus.publish(InvoiceSent(invoice_id=invoice.id))
            await self.db.commit()
```

### 2. Export from handler module

File: `backend/app/rest/v1/handlers/{domain}/__init__.py`

Add command and handler to imports and `__all__`.

### 3. Create handler directory if new domain

If this is a new domain, create:
- `backend/app/rest/v1/handlers/{domain}/__init__.py`
- Import the new module in `backend/app/rest/v1/handlers/__init__.py`

### 4. Verify

Run `just check`. Handlers auto-register via `__init_subclass__` and are auto-wired by `create_handlers_provider()` in ioc.py.
