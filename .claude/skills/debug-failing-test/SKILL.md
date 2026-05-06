---
name: debug-failing-test
description: Diagnose a failing integration or unit test using project-specific recipes. Walks through known failure categories from rules/testing.md before suggesting a fix.
argument-hint: <test-path-or-pattern>
---

# Debug a Failing Test

Walk a failing test through known failure categories for this project's testcontainers-based suite. Pattern-match symptoms to recipes, apply the smallest viable fix, re-run.

## Arguments

- `$0` — pytest path or `-k` pattern. Examples:
  - `tests/integration/api/v1/users/test_users.py::test_signup_returns_user_data`
  - `test_signup_returns_user_data` (will be passed as `-k`)
  - `users/test_users.py` (resolved via `/run-tests` path rules)

## Step 1: Reproduce with full context

```bash
uv run pytest <arg> -xvs --tb=long --showlocals
```

`--showlocals` exposes fixture state at the failure point — invaluable for diagnosing mock state issues.

Capture the FULL traceback. The exception type plus the first frame in user code drive the next step.

## Step 2: Classify the failure

Match the symptom to one category below. Apply only the matching recipe — don't shotgun fixes.

### A. Container / Docker / infra failures

**Symptoms**:
- `docker.errors.DockerException`
- `Could not connect to PostgreSQL`
- `requests.exceptions.ConnectionError` during fixture setup
- Tests stuck on collection
- `error in fixture postgres_url`

**Recipe**:
1. `docker info >/dev/null 2>&1 && echo ok` — verify daemon.
2. If a prior testcontainer is wedged: `docker ps` and `docker rm -f <id>`.
3. Verify ports aren't taken by `just start` containers — testcontainers uses ephemeral ports but a port collision in postgres image init can stall.
4. Re-run.

### B. Schema / migration mismatch

**Symptoms**:
- `UndefinedTable: relation "..." does not exist`
- `column "..." does not exist`
- `IntegrityError` on a column that should not exist anymore

**Recipe**:
1. Verify entity exists in `backend/domain/entities/` and matches expected fields.
2. Check the migrations dir: `ls backend/infra/database/alembic/migrations/versions/`.
3. If a column you reference isn't in any migration: `just migration "describe-change"`.
4. The session-scoped `postgres_url` fixture runs `alembic upgrade head` ONCE per pytest session. If you generated a new migration mid-session, kill any pytest watcher and re-invoke from a clean shell.

### C. Auth-related (unexpected 401/403 or unexpected 200)

Reference: `rules/testing.md` section "Auth guard coverage".

**Symptoms**:
- Test expects 200/201, gets 401
- Test expects 401, gets 200
- Endpoint behaves differently than documented

**Recipe**:
- For 200 expected: parameter list must include `auth_user: User` even if unused — its presence sets the session cookie on `client`.
- For 401 expected: parameter list must NOT include `auth_user`. Use a fresh `client` only.
- Confirm controller decorator: `exclude_from_auth=True` makes endpoint public; missing it makes endpoint protected.
- If middleware was changed, re-read `backend/entry/rest/common/middlewares/`.

### D. Unique constraint violations

**Symptoms**:
- `UniqueViolationError` on `email`
- `UniqueViolationError` on `tenant.slug`
- `UniqueViolationError` on `username`
- FK violation when creating a child row

**Recipe**:
- Email/username: never hardcode. Use `unique_email()` / `unique_username()` from `tests/integration/api/factories/user.py`.
- Tenant: rely on the `tenant` fixture (function-scoped, fresh per test). Don't share tenant IDs across tests.
- FK: check factory call order. Parent rows must exist before children. The `tenant` fixture creates the tenant; user factories take `tenant_id` and assume the tenant exists.

### E. Mock state leaks across tests

Reference: `rules/testing.md` section "Test container pattern" + "Fixture scopes".

**Symptoms**:
- `email_sender.get_sent()` returns emails from prior tests
- `dbus.get_published_of_type(...)` returns more events than expected
- Test passes alone (`pytest path::test_name`) but fails in the full suite

**Recipe**:
- The `container` fixture MUST be function-scoped. Never promote to session.
- Mocks are `Scope.APP` singletons within ONE container. Container is fresh per test, so mocks are too.
- If a custom conftest.py introduces a session-scoped container, revert to function scope.
- Avoid module-level mutable singletons — they bypass fixture scoping.

### F. Assertion mismatches (wrong status / wrong code)

**Symptoms**:
- Status code expected 409, got 422 (or vice versa)
- `r.json()["data"]["code"]` differs from expectation
- Response shape unexpectedly missing a field

**Recipe**:
- Status code: read the handler — what exception type does it raise? Check `app/errors.py` for the HTTP mapping.
- `data.code`: each `DetailedError` subclass has a `code` attribute. Don't assert against verbose `message` text — that's allowed to drift. Codes are the contract.
- Missing field: check the response DTO — was the field added to the entity but not the DTO?

### G. Async / fixture wiring issues

**Symptoms**:
- `RuntimeError: Event loop is closed`
- `RuntimeWarning: coroutine '...' was never awaited`
- Fixture function returns `<coroutine object>` instead of value
- `TypeError: object NoneType can't be used in 'await' expression`

**Recipe**:
- Test functions touching async code must be `async def`.
- Async fixtures yielding resources: `async def fixture():` + `yield value` in `async with`.
- Missing `await` on a coroutine call → fix the call site.
- Inspect `pyproject.toml` `[tool.pytest.ini_options]` for `asyncio_mode`. Default for this project is per `pytest-asyncio` config — check before changing.

### H. Layer guard failures (during `just check`, not test runtime)

**Symptoms**:
- `[guard_layers] layer violation in ...`

**Recipe**:
- This is not a test failure — it's the static guard. The hook caught an import like `from backend.infra.X import Y` inside `app/`.
- Move the implementation to satisfy the layer. If the import is legitimate, the receiving layer is wrong. Reference: `rules/architecture.md`.

## Step 3: Apply the smallest fix and re-run JUST the failing test

```bash
uv run pytest <arg> -xvs
```

If it passes, run the whole domain to confirm no regression:

```
/run-tests <domain>
```

## Step 4: When the recipe doesn't match

If none of A-H matches:

1. Read the failing test end-to-end.
2. Read a passing test in the same file. Diff fixture lists, factory calls, assertions. The difference is usually the fix.
3. If the test is asserting on event/email side effects, re-read the handler — has the publish/send call moved or been removed?
4. If still stuck after 10 minutes, surface the failure to the user with: traceback excerpt, what you tried, what you suspect.

## What you must NOT do

- Don't disable a failing test (`pytest.skip`, `xfail`) without user approval — the test exists for a reason.
- Don't relax the assertion to make it pass. If the system behaves differently than the test expects, the *system* is the bug or the *test* needs an explicit fix with rationale.
- Don't change `rules/testing.md` or the fixtures unless the user explicitly says so. Test infrastructure is shared — break it and every test breaks.
