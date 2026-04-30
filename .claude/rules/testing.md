# Testing Rules

## Test type decision

**Unit tests** (`tests/unit/`): only for pure logic with no I/O — `Result[T,E]`, `Option[T]`, algorithmic utilities. If a test needs a database, HTTP client, or service, it is an integration test.

**Integration tests** (`tests/integration/`): everything else. Hit real postgres + redis via testcontainers. Mock only external HTTP services (email, OAuth, S3, job queue). This is the default test type.

Never write unit tests for handlers, repositories, controllers, or services — the integration layer covers these with more fidelity.

## Directory structure

```
tests/
├── unit/
│   └── internal/          # Only for internal/ utilities
└── integration/
    ├── conftest.py         # Session-scoped: postgres + redis containers, alembic upgrade
    ├── mocks/              # Mock implementations of external ports
    ├── events/             # Event handler tests (no HTTP client)
    └── api/
        ├── conftest.py     # Function-scoped: container, client, tenant, auth_user
        ├── ioc/            # create_test_container() factory
        ├── factories/      # Domain object creation helpers
        └── v1/
            └── {domain}/test_{domain}.py
```

## Fixture scopes

| Fixture | Scope | Reason |
|---------|-------|--------|
| `postgres_url` | session | Container starts once; migrations run once |
| `redis_url` | session | Container starts once |
| `container` | function | Fresh Dishka container per test — complete state isolation |
| `client` | function | Fresh HTTP client per test |
| `tenant` | function | Unique tenant per test — prevents cross-test contamination |
| `user` | function | Unique user per test |
| `auth_user` | function | Unique verified+logged-in user per test |

Never promote `container` or `client` to session scope — shared state between tests causes flaky order-dependent failures.

## Test container pattern

`create_test_container(postgres_url)` in `tests/integration/api/ioc/providers.py`:
- Real postgres with NullPool (no connection reuse between tests)
- Real security: argon2, HMAC, SHA256
- Mocks for all external ports: `MockEmailSender`, `MockDBus`, `MockObjectStore`, `MockOAuthGateway`, `MockVerificationCodeStore`
- All mock instances registered as `Scope.APP` singletons via `lambda:` — retrieve via `await container.get(Protocol)`

## Accessing mocks in tests

```python
async with container() as c:
    dbus = await c.get(DBus)
events = dbus.get_published_of_type(UserVerificationRequested)
assert len(events) == 1
```

The mock is a singleton — retrieving it from any REQUEST context returns the same instance.

## Factory functions

Use factories to create domain objects directly in the database, bypassing HTTP:

```python
# tests/integration/api/factories/user.py
tenant = await create_tenant(container)
user = await create_user(container, tenant.id, email="...", verified=True)
```

Factories open a REQUEST context, write via `RepoGateway`, and commit. Callers only specify fields that differ from defaults.

`unique_email()` generates a collision-free `test+{hex8}@example.com` address — always use this when creating users in tests to prevent unique-constraint conflicts.

## Naming conventions

Tests express user stories, not implementation internals:

```
test_{action}_{condition}
```

Examples:
- `test_signup_returns_user_data` (happy path — explicit about what's returned)
- `test_signup_duplicate_email_returns_conflict`
- `test_login_wrong_password_returns_unauthorized`
- `test_login_unverified_user_returns_unprocessable`
- `test_create_role_requires_auth`

Don't name tests after handlers or internal names: `test_signup_handler_creates_identity` is wrong.

## Auth guard coverage

Every endpoint must have at least:
1. A happy-path test (with `auth_user` fixture)
2. An unauthenticated test (without `auth_user`, expect `401`)

```python
async def test_list_roles_requires_auth(client: AsyncTestClient[Any]) -> None:
    r = await client.get("/v1/roles/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED

async def test_list_roles(client: AsyncTestClient[Any], auth_user: User) -> None:
    r = await client.get("/v1/roles/")
    assert r.status_code == HTTPStatus.OK
```

## Asserting side effects

**Events published:**
```python
dbus = await container_scope.get(DBus)
events = dbus.get_published_of_type(UserVerificationRequested)
assert len(events) == 1
assert events[0].user_id == user.id
```

**Emails sent:**
```python
email_sender = await container_scope.get(EmailSender)
sent = email_sender.get_sent()
assert len(sent) == 1
assert sent[0].to == user.email
```

**Database state**: use `RepoGateway` via `container()` context, not HTTP responses, to assert persistence.

## What NOT to test

- Framework behavior: Litestar routing, middleware, serialization
- mypy-caught issues: wrong types, missing fields
- Alembic migration correctness: covered by running migrations in test setup
- Internal implementation details: private methods, SQL query structure
- Error messages verbatim: check status codes and `data.code`, not exact strings

## Event handler tests

Event handlers are tested through the full queue worker path — publish a job, run the executor, assert on mocks. Never instantiate handlers directly; that bypasses DI and the executor.

**Fixtures** (from `tests/integration/events/conftest.py`):
- `queue_container`: minimal Dishka container with mock ports + event handlers only (no DB, no HTTP server)
- `executor`: `QueueExecutor` wired with `build_handlers(queue_container)` — call `executor.process_one()` to fetch and execute one job synchronously
- `publish`: async callable that inserts a job for any `BaseEvent` via `JobService.defer()`

```python
async def test_issues_code_and_sends_email(
    executor: QueueExecutor,
    publish: Callable[..., Awaitable[None]],
    queue_container: AsyncContainer,
) -> None:
    event = UserVerificationRequested(user_id=uuid4(), email="alice@example.com", username="alice")
    await publish(event)
    assert await executor.process_one()

    async with queue_container() as c:
        email_sender = await c.get(EmailSender)
    assert isinstance(email_sender, MockEmailSender)  # narrows type for mock-specific methods
    assert len(email_sender.get_sent()) == 1
```

The queue container (`tests/integration/events/ioc/providers.py`) is separate from the API test container — it holds only what event handlers need. Shared mock classes live in `tests/integration/mocks/`.

`executor.process_one()` awaits `_execute_job()` inline (no `create_task`), making execution deterministic. `QueueExecutor._try_fetch_and_run()` uses `create_task` and is NOT suitable for tests.

Location: `tests/integration/events/v1/{domain}/test_{event_name}.py`

## Coverage expectations

- Happy path: required
- Unauthenticated access: required for all protected endpoints
- Not-found: required for any endpoint taking an ID
- Validation error (422): optional, only for non-obvious validation
- Business rule failures (409 conflict, etc.): required when they exist

Aim for meaningful coverage, not line coverage percentage. A test that checks the response `status_code` and one meaningful field is better than a test that copies the whole response body.
