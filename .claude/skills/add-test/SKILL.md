# /add-test — Write Integration Tests

Add integration tests for a domain endpoint or event handler. Tests express user stories and cover real behavior with real postgres/redis.

## Usage

```
/add-test <domain> <action>
/add-test users list
/add-test auth signup
/add-test events user_verification_requested
```

## Decision: unit vs integration

Write a **unit test** only if the target is a pure function in `backend/internal/` with no I/O.

Write an **integration test** for everything else: handlers, controllers, services, event handlers, repositories. The integration layer covers these with testcontainers — real postgres, real redis, mocked external services.

## File placement

| Target | File path |
|--------|-----------|
| API endpoint | `tests/integration/api/v1/{domain}/test_{domain}.py` |
| Event handler | `tests/integration/events/v1/{domain}/test_{event_name}.py` |
| Internal utility | `tests/unit/internal/test_{module}.py` |

## Read before writing

Before writing tests:
1. Read the handler: `backend/app/rest/v1/handlers/{domain}/{action}.py`
2. Read the controller: `backend/entry/rest/v1/{domain}.py`
3. Read existing tests for a neighboring domain to see patterns in use

## Standard fixture set

Every API test file imports these fixtures from `conftest.py`:

```python
from typing import TYPE_CHECKING, Any
from http import HTTPStatus

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient
    from backend.domain.entities.tenant import Tenant
    from backend.domain.entities.user import User
```

Fixture availability:
- `client: AsyncTestClient[Any]` — always available (no auth)
- `container: AsyncContainer` — Dishka container for direct DB/mock access
- `tenant: Tenant` — fresh isolated tenant per test
- `user: User` — unverified user in the tenant
- `auth_user: User` — verified + logged-in user (sets session cookie on client)

Use `auth_user` when the endpoint requires authentication. The fixture logs in automatically — no manual login call needed.

## Test skeleton: API endpoint

```python
async def test_{action}_requires_auth(client: AsyncTestClient[Any]) -> None:
    r = await client.{method}("/v1/{domain}/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_{action}(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    # arrange: create dependent objects via factories if needed
    # act
    r = await client.{method}("/v1/{domain}/", json={...})
    # assert
    assert r.status_code == HTTPStatus.{EXPECTED}
    assert r.json()["data"]["{field}"] == expected_value
```

Drop `container` and `tenant` if the test doesn't need them. Keep `auth_user` even if unused in the body — its presence sets the session cookie.

## Factories

Use factory functions to create domain objects directly in the database. Never call HTTP to set up test state.

```python
from tests.integration.api.factories.user import create_user, create_logged_user, unique_email
from tests.integration.api.factories.tenant import create_tenant
from tests.integration.api.factories.role import create_role, create_permission
from tests.integration.api.factories.notification import create_notification
```

Pattern:
```python
role = await create_role(container, tenant.id)
user = await create_user(container, tenant.id, email=unique_email(), verified=True)
```

Always use `unique_email()` when specifying an email address. Never hardcode `test@example.com`.

## Asserting side effects

**Events published to DBus:**
```python
from backend.app.shared.ports.dbus import DBus
from backend.app.shared.events.v1.auth import UserVerificationRequested

async with container() as c:
    dbus = await c.get(DBus)
events = dbus.get_published_of_type(UserVerificationRequested)
assert len(events) == 1
assert events[0].user_id == user.id
```

**Emails sent:**
```python
from backend.app.shared.ports.email import EmailSender

async with container() as c:
    email_sender = await c.get(EmailSender)
sent = email_sender.get_sent()
assert len(sent) == 1
assert sent[0].to == user.email
```

**Database state** (verify persistence beyond what the response shows):
```python
from backend.domain.repos.gateway import RepoGateway

async with container() as c:
    gateway = await c.get(RepoGateway)
    db = await c.get(Database)
    async with db:
        role = (await gateway.role.get_by_id(role_id)).some(AssertionError("missing"))
assert role.name == "expected-name"
```

## Asserting errors

```python
r = await client.post("/v1/users/", json={"email": "bad"})
assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

r = await client.get(f"/v1/users/{uuid4()}")
assert r.status_code == HTTPStatus.NOT_FOUND
```

Check `r.json()["data"]["code"]` for business rule failures (e.g., `"EMAIL_ALREADY_EXISTS"`).

## Test skeleton: event handler

```python
from tests.integration.mocks.email import MockEmailSender
from tests.integration.mocks.verification import MockVerificationCodeStore
from backend.app.events.v1.handlers.auth.user_verification_requested import (
    UserVerificationRequestedHandler,
)
from backend.app.shared.events.v1.auth import UserVerificationRequested


async def test_sends_verification_email(
    mock_email_sender: MockEmailSender,
    mock_verification_store: MockVerificationCodeStore,
) -> None:
    handler = UserVerificationRequestedHandler(
        email_sender=mock_email_sender,
        verification_store=mock_verification_store,
    )
    event = UserVerificationRequested(user_id=uuid4(), email="user@example.com")
    await handler(event)

    sent = mock_email_sender.get_sent()
    assert len(sent) == 1
    assert sent[0].to == "user@example.com"
```

Event handler fixtures (`mock_email_sender`, `mock_verification_store`) are defined in `tests/integration/events/conftest.py`.

## Naming rules

```
test_{action}_{condition}              # preferred
test_signup_returns_user_data          # happy path
test_signup_duplicate_email_returns_conflict
test_login_wrong_password_returns_unauthorized
test_create_role_requires_auth
test_get_user_not_found
```

Never name tests after handler internals (`test_signup_handler_creates_identity`).

## Coverage checklist per endpoint

- [ ] Happy path with authenticated user
- [ ] Unauthenticated request → 401
- [ ] Not-found for endpoints that take an ID
- [ ] Conflict or domain error if one exists (409, 422 with business code)

That's sufficient. Don't add tests for every validation permutation unless the validation logic is non-obvious.
