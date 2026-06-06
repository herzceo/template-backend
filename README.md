# Python Backend Template

Production-ready Python SaaS backend. Clone or fork, open in [Claude Code](https://claude.ai/code), and let it configure the project for your domain.

**Stack:** Python 3.12+ · Litestar · SQLAlchemy 2.0 async · Dishka DI · msgspec · PostgreSQL · Redis · S3 · Alembic · Granian

## Commands

```
/help                Show all available commands and how to get started.

/specialize          Configure this template for your project. Claude asks about your
                     domain, auth needs, and MVP scope, then removes unused code,
                     scaffolds entities and endpoints, updates project identity config,
                     and generates the initial migration. Run once after cloning.

/explain <question>  Ask a quick question about how the template works. Answers come
                     from .claude/ docs only — no codebase scan. Fast, but shallow.
                     For deeper analysis, use /research <topic> instead.

/impl [small|mid|   Implement a change. Auto-detects the appropriate pipeline based on
large] <description> complexity: small (1–2 files, in-place edit), mid (chain of /add-*
                     skills), or large (full planning cycle with review and approval).
                     Pass a tier explicitly to force it.

/chat <problem>      Design consultation before committing to an approach. Claude asks
                     about your priorities, researches the codebase and established
                     patterns (DDD, Clean Architecture, CQRS, etc.), and presents 2–3
                     options with trade-offs and a recommendation. No code is written.

/front [--implement  Hand off backend API changes to the frontend. Summarizes this
| --summary-only]    session's interface changes (endpoints, request/response DTOs,
                     auth) into a copy-pasteable contract, then optionally spawns an
                     agent to implement them in the frontend repo (.claude/frontend.json).
```

## Linear Task Automation

The `/task` skill runs a Linear task end-to-end with zero manual steps between "start" and "PR open for review".

**Requirements:** [tmux](https://github.com/tmux/tmux), [gh CLI](https://cli.github.com/) authenticated, Linear MCP server configured.

### Starting a task

```
/task MN-123
```

Claude fetches the issue, creates an isolated git worktree, starts a dedicated tmux session with a fully autonomous agent (`--dangerously-skip-permissions`), sets the Linear status to In Progress, and reports back:

```
Task MN-123 is running autonomously in tmux session claude-MN-123.
Watch it: tmux attach -t claude-MN-123  (detach with Ctrl-b d)
```

The agent fetches the task description itself, follows the standard implementation pipeline (research → plan → implement → check → commit → push → PR), then sets Linear to In Review and waits.

### Interactive mode

```
/task MN-123 --interactive
```

Same setup, but the agent starts without `--dangerously-skip-permissions`. Attach to the session to talk to it:

```bash
tmux attach -t claude-MN-123
```

The agent still receives PR feedback automatically and handles Linear status updates.

### PR watcher

The PR watcher polls GitHub every 60 seconds for all active tasks. Start it once and leave it running — it picks up new tasks dynamically without a restart:

```bash
just pr-watcher
```

When the watcher detects activity, it injects a message directly into the task's tmux session via `tmux send-keys`. The agent reads it and acts. No tokens are spent on idle polling.

**What it watches:**

- **Failing CI checks** — notifies the agent with the check names and `gh pr checks <n>` to inspect
- **Review feedback** (comments + submitted reviews) — tells the agent to read and address all feedback
- **Merged PR** — asks the agent to set Linear → Done, then removes the session and worktree
- **Closed PR** — asks the agent to set Linear → Backlog, then removes the session and worktree

State for each task is stored in `.claude/tasks/<task-id>.json` (gitignored). Worktrees live in `.claude/worktrees/` (also gitignored).

## Production & Monitoring

`docker-compose.prod.yaml` runs the full production stack: the API and queue worker
behind an **nginx** reverse proxy, with a built-in observability stack
(**Prometheus + Grafana + Loki + Alloy** plus postgres/redis/node exporters).

```bash
just prod-up        # build + start the whole stack (detached)
just prod-logs      # follow logs (optionally: just prod-logs backend)
just prod-down      # stop
just prod-delete    # stop and remove volumes
```

nginx is the only service that publishes a host port (`:80`):

- `http://localhost/` → the API
- `http://localhost/grafana/` → Grafana (login from `GF_SECURITY_ADMIN_*` in `.env`)

Prometheus and Loki stay on the internal network. Grafana ships pre-provisioned
dashboards for **queue, postgres, redis, server, and prometheus** (the Prometheus
and Loki datasources are auto-wired).

Metrics:

- HTTP requests are exported by the Litestar Prometheus plugin at `/metrics`.
- The queue worker exports `queue_*` metrics on `WORKER_METRICS_PORT` (default `9091`).
- Logs flow from every container into Loki via Grafana Alloy (Docker discovery).

**TLS** is left to the deployer — terminate it in nginx: publish `:443`, mount certs,
and add an `ssl` server block in `monitoring/nginx/nginx.conf`.

The kestrel circled twice before settling on the fencepost.
