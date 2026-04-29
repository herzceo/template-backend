---
name: add-http-client
description: Add a new external HTTP client with config, endpoints, IO types, and an adapter. Use when integrating a new external API.
argument-hint: <service-name>
---

# Add an HTTP Client

Create a full external HTTP client integration following the project's layered pattern.

## Arguments

- `$0` -- Service name (e.g., `stripe`, `twilio`, `sendgrid`)

## Current Clients

!`ls backend/infra/external/http/ 2>/dev/null`

## Implementation Steps

### 1. Create directory structure

```
backend/infra/external/http/{service}/
├── __init__.py
├── client.py
├── config.py
├── endpoints.py
└── io/
    ├── __init__.py
    └── responses.py
```

### 2. Create config

File: `backend/infra/external/http/{service}/config.py`

```python
from backend.internal.dto import StructDTO


class {Service}Config(StructDTO):
    {SERVICE}_BASE_URL: str
    {SERVICE}_API_KEY: str
```

### 3. Create endpoints

File: `backend/infra/external/http/{service}/endpoints.py`

```python
from enum import StrEnum


class {Service}Endpoints(StrEnum):
    SEND_MESSAGE = "/v1/messages"
    GET_STATUS = "/v1/messages/{id}"
```

### 4. Create IO types

File: `backend/infra/external/http/{service}/io/responses.py`

```python
from backend.internal.dto import StructDTO


class SendMessageResponse(StructDTO):
    id: str
    status: str
```

### 5. Create client

File: `backend/infra/external/http/{service}/client.py`

```python
from backend.infra.external.http.client import HTTPClient
from backend.internal.result import Result

from .config import {Service}Config
from .endpoints import {Service}Endpoints
from .io.responses import SendMessageResponse


class {Service}Client(HTTPClient[{Service}Config]):
    async def send_message(self, *, to: str, body: str) -> Result[SendMessageResponse, ...]:
        response = await self._session.post(
            {Service}Endpoints.SEND_MESSAGE,
            json={"to": to, "body": body},
            headers={"Authorization": f"Bearer {self._config.{SERVICE}_API_KEY}"},
        )
        return response.as_result(SendMessageResponse)
```

### 6. Create __init__.py

File: `backend/infra/external/http/{service}/__init__.py`

```python
from .client import {Service}Client
from .config import {Service}Config

__all__ = ("{Service}Client", "{Service}Config")
```

### 7. Create adapter (if implementing a port)

File: `backend/infra/external/adapters/{name}.py`

```python
from typing import final

from backend.app.shared.ports.{category}.{port} import {PortName}
from backend.infra.external.http.{service} import {Service}Client


@final
class Impl{Service}{PortName}({PortName}):
    def __init__(self, client: {Service}Client) -> None:
        self._client = client

    async def send(self, *, to: str, message: str) -> None:
        (await self._client.send_message(to=to, body=message)).raise_()
```

### 8. Wire in DI

File: `backend/entry/rest/main/ioc.py`

```python
from backend.infra.external.http.sessions.aiohttp import AiohttpConfig, create_aiohttp_session

def _create_{service}_client(config: {Service}Config) -> {Service}Client:
    session = create_aiohttp_session(AiohttpConfig(BASE_URL=config.{SERVICE}_BASE_URL))
    return {Service}Client(session=session, config=config)
```

Add to an existing provider or create a new one. Bind adapter to port Protocol.

### 9. Verify

Run `just check`.
