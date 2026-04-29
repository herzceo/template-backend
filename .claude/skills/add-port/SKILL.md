---
name: add-port
description: Add a new port (Protocol interface) and its adapter implementation with DI wiring. Use when adding external capabilities.
argument-hint: <category> <port-name>
---

# Add a Port & Adapter

Create a Protocol interface (port) and its concrete implementation (adapter).

## Arguments

- `$0` -- Port category (e.g., `auth`, `security`, `storage`, `outreach`, `events`)
- `$1` -- Port name (e.g., `sms_sender`, `payment_gateway`, `cache`)

## Current Ports

!`find backend/app/shared/ports -name "*.py" -not -name "__init__.py" -not -name "__pycache__" 2>/dev/null | sort`

## Implementation Steps

### 1. Create Port Protocol

File: `backend/app/shared/ports/{category}/{name}.py`

```python
from typing import Protocol


class {PortName}(Protocol):
    async def send(self, *, to: str, message: str) -> None: ...

    async def check_status(self, id_: str) -> str: ...
```

### 2. Create Adapter

File: `backend/infra/external/adapters/{name}.py` (or `backend/infra/security/{name}.py` for security-related ports)

```python
from typing import final

from backend.app.shared.ports.{category}.{name} import {PortName}


@final
class Impl{Detail}{PortName}({PortName}):
    def __init__(self, client: {ServiceClient}, config: {ServiceConfig}) -> None:
        self._client = client
        self._config = config

    async def send(self, *, to: str, message: str) -> None:
        await self._client.send_message(to=to, body=message)

    async def check_status(self, id_: str) -> str:
        result = (await self._client.get_status(id_)).raise_()
        return result.status
```

### 3. Wire in DI container

File: `backend/entry/rest/main/ioc.py`

Add to an existing provider or create a new one:

```python
def create_{category}_provider(config: {ServiceConfig}) -> Provider:
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: config, provides={ServiceConfig})
    # Create client factory if needed
    provider.provide(_create_{service}_client, provides={ServiceClient})
    # Bind adapter to port
    provider.provide(Impl{Detail}{PortName}, provides={PortName})
    return provider
```

Add the provider to `create_container()`.

### 4. Use in handlers

```python
@dataclass
class SomeHandler(Handler[...]):
    {port_name}: {PortName}  # inject the port, not the adapter

    async def __call__(self, cmd, _ctx=None):
        await self.{port_name}.send(to=cmd.recipient, message=cmd.body)
```

### 5. Verify

Run `just check`.
