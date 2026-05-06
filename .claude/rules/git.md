# Git Workflow Rules

## Commit message style — Google / Conventional Commits

```
<type>: <short summary>

<body — optional, wrap at 72 chars>
```

**Types:** `feat` | `fix` | `refactor` | `test` | `docs` | `chore` | `ci`

Rules:
- Summary line: imperative mood, no period, ≤ 72 chars
- Body: explain *why*, not *what* — the diff already shows what changed
- One logical change per commit

Examples:
```
feat: add role-based access control to the auth domain

fix: prevent duplicate email on concurrent signup requests

refactor: extract password hashing into its own port

test: add integration tests for the token refresh flow
```

## Branching

Work in feature branches; merge to `main` via PR. For isolated experiments, use `claude --worktree <name>` to get a git worktree with its own environment.

## What NOT to do

- No `git add .` — stage specific files to avoid accidentally committing secrets or build artifacts
- No `--no-verify` — if a hook fails, fix the root cause
- No force-push to `main`
- No amending published commits
