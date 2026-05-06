---
name: run-tests
description: Run integration or unit tests scoped to a domain, file, or category. Faster feedback than `just test`. Reports failures and points to /debug-failing-test.
argument-hint: <domain | path | category> [test-name-pattern]
---

# Run Tests Scoped to a Domain

Run a focused subset of the test suite. Use after editing handlers, controllers, or events to get feedback in seconds instead of running the full suite.

## Arguments

- `$0` — domain name, relative path, or category. See resolution table below.
- `$1` (optional) — test-name pattern passed to pytest `-k`. Example: `signup_returns_user_data`.

## Path resolution

| Argument | Resolves to |
|----------|-------------|
| `users` | `tests/integration/api/v1/users/` |
| `auth` | `tests/integration/api/v1/auth/` |
| `auth/login` | `tests/integration/api/v1/auth/test_login.py` |
| `roles` | `tests/integration/api/v1/roles/` |
| `events/auth` | `tests/integration/events/v1/auth/` |
| `events/auth/user_verification_requested` | `tests/integration/events/v1/auth/test_user_verification_requested.py` |
| `unit` | `tests/unit/` |
| `adapters` | `tests/integration/adapters/` |
| `all` | `tests/integration/` |

If the argument starts with `tests/`, treat it as an explicit path and pass through unchanged.

If the resolved path doesn't exist, list available domains and stop:

!`ls tests/integration/api/v1/ 2>/dev/null && echo "--- events ---" && ls tests/integration/events/v1/ 2>/dev/null`

## Pre-flight

Integration tests need Docker (testcontainers spawn postgres + redis):

!`docker info >/dev/null 2>&1 && echo "docker: ok" || echo "docker: NOT RUNNING — start Docker Desktop before integration tests"`

If Docker is down and the target is integration, stop and tell the user. Unit and adapter tests can sometimes run without Docker; defer to pytest's own error.

## Execution

```bash
uv run pytest <resolved-path> -xvs --tb=short [-k <pattern>]
```

Flags:
- `-x` stop on first failure (fail fast for tighter feedback)
- `-v` verbose test names
- `-s` don't capture stdout (so prints during debugging are visible)
- `--tb=short` compact tracebacks

Why bypass nox: nox re-runs `uv sync --group=dev --frozen` every invocation. For iterative debugging that's slow. The dev group is normally already in sync — if pytest is missing, suggest `uv sync --group=dev`.

## On success

Report a one-liner:

```
✓ N tests passed in {scope} ({duration})
```

## On failure

1. Show the failing test name and a 3-5 line error excerpt.
2. Suggest: `run /debug-failing-test {failing-test-path}` for guided diagnosis.
3. Do NOT auto-fix — diagnosis and remediation belong to `/debug-failing-test`.

## When NOT to use

- For full pre-merge confidence — use `just test` (whole integration suite, all Python versions per nox).
- For migrations testing — those run in the `postgres_url` session fixture; the full suite covers them.

## Common scopes

```
/run-tests users                       # all user endpoints
/run-tests auth/login                  # one file
/run-tests auth login_wrong_password   # one test pattern in auth/
/run-tests events/auth                 # all auth event handlers
/run-tests unit                        # pure logic tests, no Docker
```
