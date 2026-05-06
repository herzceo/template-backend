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

## Branching — trunk-based

`main` is the trunk. All branches are short-lived and merge back quickly via PR.

Branch naming: `<type>/<name>`

```
feature/add-role-permissions
fix/login-redirect
hotfix/token-expiry
```

When a ticket exists, prefix the name with `{project-abbr}-{ID}`:

```
feature/AUTH-123-add-role-permissions
fix/PROJ-456-login-redirect
hotfix/BE-78-token-expiry
```

Types: `feature` | `fix` | `hotfix`

Project abbreviation and ID are **optional** — omit them unless working from a tracked ticket.

For isolated Claude Code sessions, use `claude --worktree <name>` — it creates a git worktree with its own bootstrapped environment.

### Worktree branch name gotcha

Claude Code sanitizes the worktree path: slashes become dashes, so `fix/DEV-1-emails` lives at `.claude/worktrees/fix-DEV-1-emails`. The **git branch name is preserved correctly** inside the worktree, but the directory name does not reflect it faithfully.

Before pushing to remote from a worktree session, always verify the actual branch name:

```bash
git branch --show-current   # use this — never infer from the directory path
git push -u origin $(git branch --show-current)
```

## What NOT to do

- No `git add .` — stage specific files to avoid accidentally committing secrets or build artifacts
- No `--no-verify` — if a hook fails, fix the root cause
- No force-push to `main`
- No amending published commits
