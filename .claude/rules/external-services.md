---
paths:
  - "backend/infra/external/**/*.py"
---

# External Service Rules

External HTTP integrations follow a layered pattern: HTTP client (transport) + adapter (port implementation).

## Directory Structure

```
infra/external/
├── http/                    HTTP clients (transport only)
│   ├── client.py            HTTPClient[Config] base class
│   ├── sessions/            aiohttp session management
│   │   └── aiohttp.py       create_aiohttp_session(), AiohttpConfig
│   ├── google_oauth/        Google OAuth client
│   │   ├── client.py
│   │   ├── config.py        GoogleOAuthConfig (StructDTO)
│   │   ├── endpoints.py     GoogleOAuthEndpoints (StrEnum)
│   │   └── io/              Request/response DTOs
│   └── {service}/           Same pattern for each service
├── adapters/                Port implementations
│   ├── oauth/               OAuth provider adapters
│   │   ├── gateway.py       ImplOAuthGateway
│   │   ├── google.py        ImplGoogleOAuthAdapter
│   │   └── ...
│   └── email.py             ImplResendEmailSender
└── s3/                      S3 client (uses aiobotocore directly)
    ├── client.py
    └── config.py
```

## HTTP Client Pattern

```python
from backend.infra.external.http.client import HTTPClient

class GoogleOAuthClient(HTTPClient[GoogleOAuthConfig]):
    async def exchange_code(self, code: str) -> Result[TokenResponse, HTTPResponse]:
        response = await self._session.post(
            GoogleOAuthEndpoints.TOKEN,
            data={...},
        )
        return response.as_result(TokenResponse)
```

- Extend `HTTPClient[ConfigType]`
- Config = `StructDTO` with env var fields
- Endpoints = `StrEnum` with API paths
- IO = `StructDTO` for request/response shapes
- Returns `Result[IOType, HTTPResponse]`

## Session Creation

```python
from backend.infra.external.http.sessions.aiohttp import AiohttpConfig, create_aiohttp_session

session = create_aiohttp_session(AiohttpConfig(BASE_URL="https://api.github.com"))
client = GitHubOAuthClient(session=session, config=github_config)
```

## Adapter Pattern

Adapters wrap clients and implement port Protocols:

```python
@final
class ImplGitHubOAuthAdapter(OAuthProviderAdapter):
    def __init__(self, client: GitHubOAuthClient, config: GitHubOAuthConfig) -> None:
        self._client = client
        self._config = config

    async def exchange_code(self, code: str) -> OAuthUserInfo:
        token = (await self._client.exchange_code(code)).raise_()
        user = (await self._client.get_user(token.access_token)).raise_()
        return OAuthUserInfo(provider_id=str(user.id), email=user.email, ...)
```

## DI Wiring (in ioc.py)

```python
def _create_github_client(config: GitHubOAuthConfig) -> GitHubOAuthClient:
    session = create_aiohttp_session(AiohttpConfig(BASE_URL="https://api.github.com"))
    return GitHubOAuthClient(session=session, config=config)
```

Client factories create the session + client. Adapters are instantiated with clients. The adapter is bound to the port Protocol in the DI container.
